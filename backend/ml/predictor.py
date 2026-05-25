"""
predictor.py — Genera predicciones de demanda usando el MEJOR modelo
por producto según la comparación (best_model.json).
Guarda resultados en fact_predicciones con:
  - demanda_estimada
  - confianza_prediccion (R² del mejor modelo)
  - algoritmo_utilizado (nombre del algoritmo usado)
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


def _get_best_model_info(producto_id: int) -> dict:
    """Retorna info del mejor modelo para un producto desde best_model.json."""
    if os.path.exists(BEST_MODEL_PATH):
        with open(BEST_MODEL_PATH) as f:
            best = json.load(f)
        algoritmo = best.get(str(producto_id))
        if algoritmo:
            return {"algoritmo": algoritmo, "es_mejor": True}

    # Fallback: modelo legacy (.pkl)
    ruta_legacy = os.path.join(MODELS_DIR, f"{producto_id}.pkl")
    if os.path.exists(ruta_legacy):
        return {"algoritmo": "Random Forest (legacy)", "es_mejor": False}

    return None


def modelo_existe(producto_id: int) -> bool:
    """Verifica si existe algún modelo (best o legacy) para el producto."""
    if os.path.exists(os.path.join(MODELS_DIR, f"best_{producto_id}.pkl")):
        return True
    if os.path.exists(os.path.join(MODELS_DIR, f"{producto_id}.pkl")):
        return True
    return False


def cargar_modelo(producto_id: int):
    """Carga el mejor modelo disponible (best_{id}.pkl > {id}.pkl)."""
    ruta_best = os.path.join(MODELS_DIR, f"best_{producto_id}.pkl")
    if os.path.exists(ruta_best):
        return joblib.load(ruta_best)
    ruta_legacy = os.path.join(MODELS_DIR, f"{producto_id}.pkl")
    if os.path.exists(ruta_legacy):
        return joblib.load(ruta_legacy)
    raise FileNotFoundError(f"No hay modelo para producto_id={producto_id}. Entrena primero.")


def _get_r2_del_modelo(producto_id: int, algoritmo: str = None) -> float:
    """Lee el R² guardado del mejor modelo o del legacy."""
    # Intentar best model meta
    meta_path = os.path.join(MODELS_DIR, f"best_{producto_id}_meta.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
            r2 = meta.get("r2")
            if r2 is not None:
                return r2

    # Fallback: legacy meta
    meta_legacy = os.path.join(MODELS_DIR, f"{producto_id}_meta.json")
    if os.path.exists(meta_legacy):
        with open(meta_legacy) as f:
            return json.load(f).get("r2", 0.0)

    return 0.0


async def generar_predicciones(n_dias: int = 7) -> dict:
    """
    Genera predicciones para todos los productos con modelos entrenados.
    Usa el MEJOR modelo según la comparación.
    """
    db = SessionLocal()
    try:
        # Cargar datos históricos
        ventas = db.query(
            models.FactVenta.producto_id,
            models.FactVenta.fecha,
            models.FactVenta.cantidad_vendida,
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

        # Obtener clima futuro
        try:
            pronostico_api = await obtener_pronostico_pacasmayo(n_dias)
        except Exception:
            pronostico_api = []

        clima_futuro_rows = []
        if pronostico_api:
            print(f"[ML] Usando pronóstico REAL de API para {n_dias} días.")
            for p in pronostico_api:
                clima_futuro_rows.append({
                    "fecha": pd.Timestamp(p["fecha"]),
                    "temperatura_promedio": p["temperatura_promedio"],
                    "condicion": p["condicion"],
                    "es_feriado": False,
                    "evento_especial": None,
                })
        else:
            print("[AVISO] API de clima falló. Usando promedios históricos de respaldo.")
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

        # Limpiar predicciones existentes (hoy en adelante)
        db.query(models.FactPrediccion).filter(
            models.FactPrediccion.fecha_proyectada >= hoy
        ).delete(synchronize_session=False)
        db.commit()

        predicciones_guardadas = []

        for prod_id, prod_nombre in productos:
            if not modelo_existe(prod_id):
                continue

            modelo = cargar_modelo(prod_id)
            info = _get_best_model_info(prod_id)
            algoritmo = info["algoritmo"] if info else "Random Forest (legacy)"
            r2 = _get_r2_del_modelo(prod_id, algoritmo)

            df_fut = build_future_features(df_ventas, df_clima_futuro, prod_id, n_dias)

            for _, row_feat in df_fut.iterrows():
                X_pred = row_feat[FEATURE_COLS].values.reshape(1, -1)
                demanda = float(max(0, round(modelo.predict(X_pred)[0])))
                fecha_pred = row_feat["fecha"].date()

                db_pred = models.FactPrediccion(
                    producto_id=prod_id,
                    fecha_proyectada=fecha_pred,
                    demanda_estimada=demanda,
                    confianza_prediccion=r2,
                    algoritmo_utilizado=algoritmo,
                )
                db.add(db_pred)
                predicciones_guardadas.append({
                    "producto_id": prod_id,
                    "producto_nombre": prod_nombre,
                    "fecha_proyectada": str(fecha_pred),
                    "demanda_estimada": demanda,
                    "confianza_prediccion": r2,
                    "algoritmo_utilizado": algoritmo,
                })

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
