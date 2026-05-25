"""
trainer.py — Entrenamiento de TODOS los modelos predictivos
Usa el comparador para entrenar y evaluar 7 algoritmos por producto.
Guarda:
  - models_trained/best_{id}.pkl  (mejor modelo por producto)
  - models_trained/best_{id}_meta.json  (métricas de todos los modelos)
  - models_trained/best_model.json  (mapeo rápido producto → mejor algoritmo)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Forzar stdout a UTF-8 para evitar UnicodeEncodeError en Windows
if sys.stdout.encoding and sys.stdout.encoding.upper() not in ("UTF-8", "UTF8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from datetime import date
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from database import SessionLocal
import models
from ml.features import build_features, get_X_y, FEATURE_COLS
from ml.comparador import entrenar_y_comparar_todos

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models_trained")
os.makedirs(MODELS_DIR, exist_ok=True)


def entrenar_todos():
    """
    Entrena y compara TODOS los modelos para cada producto.
    Retorna el reporte completo del comparador.
    """
    print("[TRAINER] Iniciando entrenamiento y comparación de 7 modelos...")
    print("[TRAINER] Modelos: Random Forest, Linear Regression, Gradient Boosting,")
    print("[TRAINER]          SARIMA, Prophet, MLP Neural Network, Ensemble")

    resultado = entrenar_y_comparar_todos()

    if "error" in resultado:
        print(f"[TRAINER] ERROR: {resultado['error']}")
    else:
        print(f"[TRAINER] OK: {resultado['productos_con_modelo']} productos entrenados")
        for algo, count in resultado.get("resumen_algoritmos", {}).items():
            print(f"  {algo}: {count} productos")

    return resultado


def entrenar_solo_random_forest():
    """
    Entrena SOLO Random Forest (compatibilidad hacia atrás).
    Útil si no se quiere esperar el entrenamiento completo de 7 modelos.
    """
    print("[TRAINER] Entrenando solo Random Forest (modo legacy)...")

    df_ventas, df_clima, df_productos = _cargar_datos()
    if df_ventas.empty:
        return {"error": "No hay datos de ventas en la BD. Ejecuta primero el seed de datos."}

    df_features = build_features(df_ventas, df_clima)
    resultados = []

    for _, row in df_productos.iterrows():
        pid = int(row["id"])
        nombre = row["nombre"]
        print(f"  -> Entrenando Random Forest para: {nombre} (id={pid})...")

        metricas = _entrenar_rf_producto(df_features, pid, nombre)
        resultados.append(metricas)
        if "error" not in metricas:
            print(f"     MAE={metricas['mae']} | R2={metricas['r2']}")

    return {"modelos": resultados}


def _cargar_datos():
    db = SessionLocal()
    try:
        ventas = db.query(
            models.FactVenta.producto_id,
            models.FactVenta.fecha,
            models.FactVenta.cantidad_vendida,
        ).all()
        df_ventas = pd.DataFrame(ventas, columns=["producto_id", "fecha", "cantidad_vendida"])

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

        productos = db.query(models.DimProducto.id, models.DimProducto.nombre).all()
        df_productos = pd.DataFrame(productos, columns=["id", "nombre"])

        return df_ventas, df_clima, df_productos
    finally:
        db.close()


def _entrenar_rf_producto(df_features, producto_id, nombre):
    import json
    import joblib

    df_prod = df_features[df_features["producto_id"] == producto_id].copy()
    if len(df_prod) < 30:
        return {"error": f"Datos insuficientes para {nombre}: {len(df_prod)} registros"}

    X, y = get_X_y(df_prod)
    X_train, X_test = X[:-30], X[-30:]
    y_train, y_test = y[:-30], y[-30:]

    modelo = RandomForestRegressor(
        n_estimators=200, max_depth=8, min_samples_split=5,
        min_samples_leaf=3, max_features="sqrt", random_state=42, n_jobs=-1,
    )
    modelo.fit(X_train, y_train)

    y_pred = np.maximum(modelo.predict(X_test), 0)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    importancias = dict(zip(FEATURE_COLS, modelo.feature_importances_))
    top3 = sorted(importancias.items(), key=lambda x: x[1], reverse=True)[:3]

    ruta_modelo = os.path.join(MODELS_DIR, f"{producto_id}.pkl")
    joblib.dump(modelo, ruta_modelo)

    meta = {
        "producto_id": producto_id,
        "nombre": nombre,
        "r2": round(r2, 4),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "algoritmo": "Random Forest",
    }
    ruta_meta = os.path.join(MODELS_DIR, f"{producto_id}_meta.json")
    with open(ruta_meta, "w") as f:
        json.dump(meta, f, indent=2)

    return {
        "producto_id": producto_id,
        "nombre": nombre,
        "n_registros_entrenamiento": len(X_train),
        "n_registros_test": len(X_test),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "r2": round(r2, 4),
        "top3_features": [f"{k}: {v:.3f}" for k, v in top3],
        "modelo_guardado": ruta_modelo,
        "algoritmo": "Random Forest",
    }


if __name__ == "__main__":
    resultado = entrenar_todos()
    if "error" not in resultado:
        for m in resultado.get("detalle_por_producto", []):
            if m.get("mejor_modelo"):
                print(f"  [OK] {m['producto_nombre']}: mejor={m['mejor_modelo']} RMSE={m['mejor_rmse']}")
            else:
                print(f"  [--] {m['producto_nombre']}: {m.get('error', 'sin modelo')}")
