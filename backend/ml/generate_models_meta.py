"""
generate_models_meta.py — Genera/actualiza metadatos de modelos entrenados (OE6)
=================================================================================
Lee los modelos .pkl en models_trained/ y genera/actualiza los archivos
best_{id}_meta.json con métricas: RMSE, MAE, R², algoritmo utilizado.

También genera un resumen global: models_trained/resumen_modelos.json
con las métricas promedio de todos los productos para el artículo de tesis.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import joblib
import numpy as np
import pandas as pd
from datetime import date, timedelta
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from database import SessionLocal
import models
from ml.features import build_features, get_X_y, FEATURE_COLS

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models_trained")


def cargar_datos():
    db = SessionLocal()
    try:
        ventas = db.query(
            models.FactVenta.producto_id,
            models.FactVenta.fecha,
            models.FactVenta.cantidad_vendida,
        ).all()
        df_ventas = pd.DataFrame(ventas, columns=["producto_id", "fecha", "cantidad_vendida"])
        df_ventas["fecha"] = pd.to_datetime(df_ventas["fecha"])

        clima = db.query(
            models.DimClima.fecha,
            models.DimClima.temperatura_promedio,
            models.DimClima.condicion,
            models.DimClima.es_feriado,
            models.DimClima.evento_especial,
        ).all()
        df_clima = pd.DataFrame(
            clima,
            columns=["fecha", "temperatura_promedio", "condicion", "es_feriado", "evento_especial"]
        )
        df_clima["fecha"] = pd.to_datetime(df_clima["fecha"])

        productos = db.query(models.DimProducto.id, models.DimProducto.nombre).all()
        df_productos = pd.DataFrame(productos, columns=["id", "nombre"])

        return df_ventas, df_clima, df_productos
    finally:
        db.close()


def evaluar_modelo(modelo, df_features, producto_id):
    """Evalúa un modelo y retorna métricas MAE, RMSE, R²."""
    df_prod = df_features[df_features["producto_id"] == producto_id].copy()
    if len(df_prod) < 20:
        return None

    X, y = get_X_y(df_prod)
    # Usar últimos 30 días como test si hay suficientes datos
    n_test = min(30, len(X) // 4)
    if n_test < 5:
        return None

    X_test = X[-n_test:]
    y_test = y[-n_test:]

    try:
        if hasattr(modelo, 'forecast') and callable(getattr(modelo, 'forecast', None)):
            y_pred = np.array([max(0, modelo.forecast(steps=1)[0])] * n_test)
        else:
            y_pred = np.maximum(0, modelo.predict(X_test))

        mae  = float(mean_absolute_error(y_test, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        r2   = float(r2_score(y_test, y_pred))

        return {
            "mae":  round(mae, 4),
            "rmse": round(rmse, 4),
            "r2":   round(r2, 4),
            "n_test": n_test,
        }
    except Exception as e:
        print(f"    [WARN] Error evaluando modelo: {e}")
        return None


def main():
    print("=" * 60)
    print("  GENERATE MODELS META — Panadería Victoria (OE6)")
    print("=" * 60)

    if not os.path.exists(MODELS_DIR):
        print(f"[ERROR] Directorio de modelos no existe: {MODELS_DIR}")
        print("        Ejecuta primero: POST /ml/entrenar")
        return

    print("\n[INFO] Cargando datos de la BD...")
    df_ventas, df_clima, df_productos = cargar_datos()

    if df_ventas.empty:
        print("[ERROR] No hay datos de ventas en la BD.")
        return

    print(f"[OK] {len(df_ventas)} registros de ventas | {len(df_productos)} productos")

    # Construir features una sola vez
    print("[INFO] Construyendo features...")
    df_features = build_features(df_ventas, df_clima)
    print(f"[OK] {len(df_features)} filas de features generadas")

    # Leer best_model.json si existe
    best_model_path = os.path.join(MODELS_DIR, "best_model.json")
    best_model_map = {}
    if os.path.exists(best_model_path):
        with open(best_model_path) as f:
            best_model_map = json.load(f)

    # Procesar cada producto
    resumen = []
    productos_procesados = 0

    print("\n[INFO] Evaluando modelos por producto...")
    for _, row in df_productos.iterrows():
        pid = int(row["id"])
        nombre = str(row["nombre"])

        # Buscar modelo best_ o legacy
        ruta_best = os.path.join(MODELS_DIR, f"best_{pid}.pkl")
        ruta_legacy = os.path.join(MODELS_DIR, f"{pid}.pkl")

        ruta_modelo = None
        algoritmo = best_model_map.get(str(pid), "Random Forest")

        if os.path.exists(ruta_best):
            ruta_modelo = ruta_best
        elif os.path.exists(ruta_legacy):
            ruta_modelo = ruta_legacy
            algoritmo = "Random Forest (legacy)"

        if ruta_modelo is None:
            print(f"  [--] {nombre}: sin modelo .pkl")
            continue

        print(f"  [>>] {nombre} (id={pid}) — {algoritmo}...")

        try:
            modelo = joblib.load(ruta_modelo)
        except Exception as e:
            print(f"       [ERROR] No se pudo cargar el modelo: {e}")
            continue

        metricas = evaluar_modelo(modelo, df_features, pid)

        if metricas is None:
            print(f"       [SKIP] Datos insuficientes para evaluar")
            continue

        print(f"       MAE={metricas['mae']:.2f} | RMSE={metricas['rmse']:.2f} | R²={metricas['r2']:.4f}")

        # Actualizar/crear best_{pid}_meta.json
        meta_path = os.path.join(MODELS_DIR, f"best_{pid}_meta.json")
        meta_existente = {}
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta_existente = json.load(f)

        meta_existente.update({
            "producto_id": pid,
            "nombre": nombre,
            "algoritmo": algoritmo,
            "mae":  metricas["mae"],
            "rmse": metricas["rmse"],
            "r2":   metricas["r2"],
            "n_test": metricas["n_test"],
            "generado_por": "generate_models_meta.py",
        })

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_existente, f, indent=2, ensure_ascii=False)

        # También actualizar archivo legacy si existe
        legacy_meta = os.path.join(MODELS_DIR, f"{pid}_meta.json")
        if os.path.exists(legacy_meta):
            with open(legacy_meta, "w", encoding="utf-8") as f:
                json.dump(meta_existente, f, indent=2, ensure_ascii=False)

        resumen.append({
            "producto_id": pid,
            "nombre": nombre,
            "algoritmo": algoritmo,
            "mae":  metricas["mae"],
            "rmse": metricas["rmse"],
            "r2":   metricas["r2"],
        })
        productos_procesados += 1

    # Guardar resumen global
    if resumen:
        maes  = [r["mae"]  for r in resumen]
        rmses = [r["rmse"] for r in resumen]
        r2s   = [r["r2"]   for r in resumen]

        resumen_global = {
            "total_productos": productos_procesados,
            "mae_promedio":    round(float(np.mean(maes)),  4),
            "mae_min":         round(float(np.min(maes)),   4),
            "mae_max":         round(float(np.max(maes)),   4),
            "rmse_promedio":   round(float(np.mean(rmses)), 4),
            "rmse_min":        round(float(np.min(rmses)),  4),
            "rmse_max":        round(float(np.max(rmses)),  4),
            "r2_promedio":     round(float(np.mean(r2s)),   4),
            "r2_max":          round(float(np.max(r2s)),    4),
            "r2_min":          round(float(np.min(r2s)),    4),
            "detalle":         resumen,
        }

        ruta_resumen = os.path.join(MODELS_DIR, "resumen_modelos.json")
        with open(ruta_resumen, "w", encoding="utf-8") as f:
            json.dump(resumen_global, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 60)
        print("  RESUMEN DE MÉTRICAS (para artículo de tesis)")
        print("=" * 60)
        print(f"  Productos evaluados : {productos_procesados}")
        print(f"  MAE  promedio       : {resumen_global['mae_promedio']:.4f}")
        print(f"  RMSE promedio       : {resumen_global['rmse_promedio']:.4f}")
        print(f"  R²   promedio       : {resumen_global['r2_promedio']:.4f}")
        print(f"  R²   máximo         : {resumen_global['r2_max']:.4f}")
        print(f"\n  Guardado en: {ruta_resumen}")
        print("=" * 60)
        print("\n[DONE] Metadatos generados exitosamente.")
    else:
        print("\n[WARN] No se pudo evaluar ningún producto. ¿Hay modelos entrenados?")


if __name__ == "__main__":
    main()
