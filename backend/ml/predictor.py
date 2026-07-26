"""
predictor.py â€” Genera predicciones de demanda usando el MEJOR modelo
por producto segÃºn la comparaciÃ³n (best_model.json).
Guarda resultados en fact_predicciones con:
  - demanda_estimada
  - confianza_prediccion (RÂ² del mejor modelo)
  - algoritmo_utilizado (nombre del algoritmo usado)

Optimizaciones aplicadas:
  - Cache de modelos en memoria (evita 24 joblib.load() por request)
  - Cache de best_model.json y RÂ² metadatos
  - Batch predict (un solo .predict() por producto en vez de per-row)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import joblib
import numpy as np
import pandas as pd
from datetime import date, timedelta

from database import SessionLocal
import models
from ml.features import (
    build_features, build_future_features, FEATURE_COLS, CONDICION_MAP
)
from ml.weather_api import obtener_pronostico_pacasmayo

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models_trained")
BEST_MODEL_PATH = os.path.join(MODELS_DIR, "best_model.json")

_MODEL_CACHE = {}  # key: (producto_id, algoritmo_name) â†’ model
_BEST_MODEL_CACHE = None
_BEST_MODEL_CACHE_MTIME = 0
_R2_CACHE = {}


def invalidar_cache():
    _MODEL_CACHE.clear()
    _R2_CACHE.clear()
    global _BEST_MODEL_CACHE, _BEST_MODEL_CACHE_MTIME
    _BEST_MODEL_CACHE = None
    _BEST_MODEL_CACHE_MTIME = 0


def _load_best_model_json():
    global _BEST_MODEL_CACHE, _BEST_MODEL_CACHE_MTIME
    if not os.path.exists(BEST_MODEL_PATH):
        _BEST_MODEL_CACHE = {}
        _BEST_MODEL_CACHE_MTIME = 0
        return _BEST_MODEL_CACHE
    mtime = os.path.getmtime(BEST_MODEL_PATH)
    if _BEST_MODEL_CACHE is None or mtime > _BEST_MODEL_CACHE_MTIME:
        with open(BEST_MODEL_PATH) as f:
            _BEST_MODEL_CACHE = json.load(f)
        _BEST_MODEL_CACHE_MTIME = mtime
    return _BEST_MODEL_CACHE


def _get_best_model_info(producto_id: int) -> dict:
    """Retorna info del mejor modelo para un producto desde best_model.json."""
    best = _load_best_model_json()
    algoritmo = best.get(str(producto_id))
    if algoritmo:
        return {"algoritmo": algoritmo, "es_mejor": True}

    ruta_legacy = os.path.join(MODELS_DIR, f"{producto_id}.pkl")
    if os.path.exists(ruta_legacy):
        return {"algoritmo": "Random Forest (legacy)", "es_mejor": False}

    return None


def modelo_existe(producto_id: int) -> bool:
    """Verifica si existe algÃºn modelo (best o legacy) para el producto."""
    if os.path.exists(os.path.join(MODELS_DIR, f"best_{producto_id}.pkl")):
        return True
    if os.path.exists(os.path.join(MODELS_DIR, f"{producto_id}.pkl")):
        return True
    return False


def cargar_modelo(producto_id: int):
    """Carga el mejor modelo disponible con cache en memoria."""
    key = (producto_id, None)
    if key in _MODEL_CACHE:
        return _MODEL_CACHE[key]

    ruta_best = os.path.join(MODELS_DIR, f"best_{producto_id}.pkl")
    if os.path.exists(ruta_best):
        modelo = joblib.load(ruta_best)
    else:
        ruta_legacy = os.path.join(MODELS_DIR, f"{producto_id}.pkl")
        if os.path.exists(ruta_legacy):
            modelo = joblib.load(ruta_legacy)
        else:
            raise FileNotFoundError(f"No hay modelo para producto_id={producto_id}. Entrena primero.")

    _MODEL_CACHE[key] = modelo
    return modelo


def _get_r2_del_modelo(producto_id: int, algoritmo: str = None) -> float:
    """Lee el RÂ² guardado del mejor modelo con cache en memoria."""
    if producto_id in _R2_CACHE:
        return _R2_CACHE[producto_id]

    meta_path = os.path.join(MODELS_DIR, f"best_{producto_id}_meta.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
            r2 = meta.get("r2")
            if r2 is not None:
                _R2_CACHE[producto_id] = r2
                return r2

    meta_legacy = os.path.join(MODELS_DIR, f"{producto_id}_meta.json")
    if os.path.exists(meta_legacy):
        with open(meta_legacy) as f:
            r2 = json.load(f).get("r2", 0.0)
            _R2_CACHE[producto_id] = r2
            return r2

    _R2_CACHE[producto_id] = 0.0
    return 0.0


def cargar_todos_modelos(prod_id: int):
    """Carga todos los modelos guardados para un producto.
    Retorna lista de (model, algoritmo, r2, es_mejor)."""
    resultados = []

    try:
        model = cargar_modelo(prod_id)
        info = _get_best_model_info(prod_id)
        algo = info["algoritmo"] if info else "Random Forest (legacy)"
        r2 = _get_r2_del_modelo(prod_id, algo)
        resultados.append((model, algo, r2, True))
    except FileNotFoundError:
        pass

    meta_path = os.path.join(MODELS_DIR, f"best_{prod_id}_meta.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
        mejores_info = _get_best_model_info(prod_id)
        mejor_algo = mejores_info["algoritmo"] if mejores_info else None
        modelos_guardados = meta.get("modelos_guardados", {})
        for safe_name, algo_name in modelos_guardados.items():
            if algo_name == mejor_algo:
                continue
            model_path = os.path.join(MODELS_DIR, f"model_{safe_name}_{prod_id}.pkl")
            if os.path.exists(model_path):
                key = (prod_id, algo_name)
                if key in _MODEL_CACHE:
                    model = _MODEL_CACHE[key]
                else:
                    model = joblib.load(model_path)
                    _MODEL_CACHE[key] = model
                r2 = next(
                    (r.get("r2", 0) for r in meta.get("todos_resultados", [])
                     if r.get("algoritmo") == algo_name and "r2" in r),
                    0,
                )
                resultados.append((model, algo_name, r2, False))

    return resultados


async def generar_predicciones(n_dias: int = 7) -> dict:
    """
    Genera predicciones para todos los productos con TODOS los modelos entrenados.
    Guarda una fila por (producto Ã— fecha Ã— algoritmo).
    """
    db = SessionLocal()
    try:
        desde = date.today() - timedelta(days=60)
        ventas = db.query(
            models.FactVenta.producto_id,
            models.FactVenta.fecha,
            models.FactVenta.cantidad_vendida,
        ).filter(
            models.FactVenta.fecha >= desde
        ).all()
        df_ventas = pd.DataFrame(ventas, columns=["producto_id", "fecha", "cantidad_vendida"])
        df_ventas["fecha"] = pd.to_datetime(df_ventas["fecha"])

        clima_hist = db.query(
            models.DimClima.fecha,
            models.DimClima.temperatura_promedio,
            models.DimClima.condicion,
            models.DimClima.es_feriado,
            models.DimClima.evento_especial,
        ).all()
        df_clima = pd.DataFrame(
            clima_hist,
            columns=["fecha", "temperatura_promedio", "condicion", "es_feriado", "evento_especial"]
        )
        df_clima["fecha"] = pd.to_datetime(df_clima["fecha"])

        productos = db.query(models.DimProducto.id, models.DimProducto.nombre).all()

        hoy = date.today()
        fechas_futuras = [hoy + timedelta(days=i + 1) for i in range(n_dias)]

        try:
            pronostico_api = await obtener_pronostico_pacasmayo(n_dias)
        except Exception:
            pronostico_api = []

        clima_futuro_rows = []
        if pronostico_api:
            print(f"[ML] Usando pronostico REAL de API para {n_dias} dias.")
            for p in pronostico_api:
                clima_futuro_rows.append({
                    "fecha": pd.Timestamp(p["fecha"]),
                    "temperatura_promedio": p["temperatura_promedio"],
                    "condicion": p["condicion"],
                    "es_feriado": False,
                    "evento_especial": None,
                })
        else:
            print("[AVISO] API de clima fallo. Usando promedios historicos de respaldo.")
            for f in fechas_futuras:
                mes_hist = df_clima[df_clima["fecha"].dt.month == f.month]
                temp_media = mes_hist["temperatura_promedio"].mean() if not mes_hist.empty else 22.0
                clima_futuro_rows.append({
                    "fecha": pd.Timestamp(f),
                    "temperatura_promedio": round(temp_media + np.random.normal(0, 1), 1),
                    "condicion": "Soleado",
                    "es_feriado": False,
                    "evento_especial": None,
                })

        df_clima_futuro = pd.DataFrame(clima_futuro_rows)

        db.query(models.FactPrediccion).delete()
        db.commit()

        predicciones_guardadas = []

        for prod_id, prod_nombre in productos:
            if not modelo_existe(prod_id):
                continue

            for model, algoritmo, r2, es_mejor in cargar_todos_modelos(prod_id):
                try:
                    predicted_values = []
                    for dia_idx in range(n_dias):
                        df_fut_dia = build_future_features(df_ventas, df_clima_futuro, prod_id, n_dias, predicted_values=predicted_values[:dia_idx])
                        X_dia = df_fut_dia.iloc[[dia_idx]][FEATURE_COLS].values
                        if hasattr(model, 'forecast') and callable(getattr(model, 'forecast', None)):
                            pred = model.forecast(steps=1)[0]
                        else:
                            pred = model.predict(X_dia)[0]
                        pred = float(np.maximum(0, np.round(pred)))
                        predicted_values.append(pred)
                        fecha_pred = df_clima_futuro.iloc[dia_idx]["fecha"]
                        if isinstance(fecha_pred, pd.Timestamp):
                            fecha_pred = fecha_pred.date()
                        confianza_norm = None
                        if r2 is not None and not np.isnan(r2):
                            confianza_norm = max(0.0, min(0.999, float(r2)))

                        db_pred = models.FactPrediccion(
                            producto_id=prod_id,
                            fecha_proyectada=fecha_pred,
                            demanda_estimada=pred,
                            confianza_prediccion=confianza_norm,
                            algoritmo_utilizado=algoritmo,
                        )
                        db.add(db_pred)
                        predicciones_guardadas.append({
                            "producto_id": prod_id,
                            "producto_nombre": prod_nombre,
                            "fecha_proyectada": str(fecha_pred),
                            "demanda_estimada": pred,
                            "confianza_prediccion": confianza_norm,
                            "algoritmo_utilizado": algoritmo,
                        })
                except Exception as e:
                    print(f"[AVISO] Modelo '{algoritmo}' para producto {prod_id} fallo: {e}")
                    continue

        db.commit()

        return {
            "status": "ok",
            "n_dias": n_dias,
            "total_predicciones": len(predicciones_guardadas),
            "predicciones": predicciones_guardadas,
        }

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    import asyncio
    resultado = asyncio.run(generar_predicciones(n_dias=7))
    print(f"[OK] {resultado['total_predicciones']} predicciones generadas")
    for p in resultado["predicciones"][:5]:
        print(f"  {p['producto_nombre']} | {p['fecha_proyectada']} -> {p['demanda_estimada']} uds [{p['algoritmo_utilizado']}]")


