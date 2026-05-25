"""
comparador.py — Entrena TODOS los modelos disponibles, los compara
por producto, y guarda el mejor modelo + un ranking global.

Flujo:
  1. Cargar datos (ventas + clima)
  2. Construir features (mismo pipeline que features.py)
  3. Por cada producto:
     a. Entrenar cada modelo del registry
     b. Evaluar en test set (últimos 30 días)
     c. Guardar métricas de todos los modelos
     d. Elegir el mejor (por RMSE)
  4. Guardar best_model.json: {producto_id: "nombre_del_mejor_algoritmo"}
  5. Retornar reporte completo con ranking
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

import json
import joblib
import numpy as np
import pandas as pd

from database import SessionLocal
import models as db_models
from ml.features import build_features, get_X_y, FEATURE_COLS

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models_trained")
os.makedirs(MODELS_DIR, exist_ok=True)

BEST_MODEL_PATH = os.path.join(MODELS_DIR, "best_model.json")


def cargar_datos_desde_db():
    """Carga ventas y clima desde PostgreSQL como DataFrames."""
    db = SessionLocal()
    try:
        ventas = db.query(
            db_models.FactVenta.producto_id,
            db_models.FactVenta.fecha,
            db_models.FactVenta.cantidad_vendida,
        ).all()
        df_ventas = pd.DataFrame(ventas, columns=["producto_id", "fecha", "cantidad_vendida"])

        clima = db.query(
            db_models.DimClima.fecha,
            db_models.DimClima.temperatura_promedio,
            db_models.DimClima.condicion,
            db_models.DimClima.es_feriado,
            db_models.DimClima.evento_especial,
        ).all()
        df_clima = pd.DataFrame(
            clima,
            columns=["fecha", "temperatura_promedio", "condicion", "es_feriado", "evento_especial"]
        )

        productos = db.query(db_models.DimProducto.id, db_models.DimProducto.nombre).all()
        df_productos = pd.DataFrame(productos, columns=["id", "nombre"])

        return df_ventas, df_clima, df_productos
    finally:
        db.close()


def entrenar_y_comparar_todos():
    """
    Entrena todos los modelos para cada producto, compara resultados
    y guarda el mejor modelo por producto.
    """
    from ml.models.registry import MODEL_REGISTRY, get_all_models

    print("=" * 60)
    print("[COMPARADOR] Iniciando comparación de modelos...")
    print(f"[COMPARADOR] Modelos disponibles: {list(MODEL_REGISTRY.keys())}")
    print("=" * 60)

    df_ventas, df_clima, df_productos = cargar_datos_desde_db()

    if df_ventas.empty:
        return {"error": "No hay datos de ventas en la BD. Ejecuta primero el seed de datos."}

    print(f"[COMPARADOR] Construyendo features para {len(df_productos)} productos...")
    df_features = build_features(df_ventas, df_clima)

    ranking_global = []
    best_models = {}
    modelos_disponibles = get_all_models()

    for _, prod_row in df_productos.iterrows():
        pid = int(prod_row["id"])
        nombre = prod_row["nombre"]
        print(f"\n{'-' * 50}")
        print(f"[COMPARADOR] Producto: {nombre} (id={pid})")

        df_prod = df_features[df_features["producto_id"] == pid].copy()
        if len(df_prod) < 30:
            print(f"  -> Datos insuficientes: {len(df_prod)} registros (min 30)")
            ranking_global.append({
                "producto_id": pid, "producto_nombre": nombre,
                "n_registros": len(df_prod), "mejor_modelo": None,
                "resultados": [], "error": "Datos insuficientes",
            })
            continue

        X, y = get_X_y(df_prod)
        X_train, X_test = X[:-30], X[-30:]
        y_train, y_test = y[:-30], y[-30:]

        resultados_modelos = []
        mejor_rmse = float("inf")
        mejor_nombre = None
        mejor_modelo_obj = None

        for algo_nombre, ModeloClase in modelos_disponibles:
            try:
                print(f"  -> Entrenando {algo_nombre}...", end=" ")
                modelo = ModeloClase()
                modelo.train(X_train, y_train)
                metricas = modelo.evaluate(X_test, y_test)

                resultados_modelos.append({
                    "algoritmo": algo_nombre,
                    "mae": metricas["mae"],
                    "rmse": metricas["rmse"],
                    "r2": metricas["r2"],
                })

                print(f"MAE={metricas['mae']} RMSE={metricas['rmse']} R2={metricas['r2']}")

                if metricas["rmse"] < mejor_rmse:
                    mejor_rmse = metricas["rmse"]
                    mejor_nombre = algo_nombre
                    mejor_modelo_obj = modelo

            except Exception as e:
                print(f"  -> {algo_nombre} ERROR (omitido): {e}")
                resultados_modelos.append({
                    "algoritmo": algo_nombre,
                    "error": str(e)[:200],
                })

        # Guardar el mejor modelo
        if mejor_modelo_obj and mejor_nombre:
            safe_name = mejor_nombre.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("+", "plus")
            model_path = os.path.join(MODELS_DIR, f"best_{pid}.pkl")
            meta_path = os.path.join(MODELS_DIR, f"best_{pid}_meta.json")

            joblib.dump(mejor_modelo_obj.model, model_path)
            with open(meta_path, "w") as f:
                json.dump({
                    "producto_id": pid,
                    "producto_nombre": nombre,
                    "mejor_algoritmo": mejor_nombre,
                    "rmse": round(mejor_rmse, 2),
                    "mae": round(
                        next((r["mae"] for r in resultados_modelos if r.get("algoritmo") == mejor_nombre and "mae" in r), 0), 2
                    ),
                    "r2": round(
                        next((r["r2"] for r in resultados_modelos if r.get("algoritmo") == mejor_nombre and "r2" in r), 0), 4
                    ),
                    "todos_resultados": resultados_modelos,
                }, f, indent=2, default=str)

            best_models[str(pid)] = mejor_nombre
            print(f"  >>> MEJOR modelo para {nombre}: {mejor_nombre} (RMSE={mejor_rmse})")

        ranking_global.append({
            "producto_id": pid,
            "producto_nombre": nombre,
            "n_registros": len(df_prod),
            "n_train": len(X_train),
            "n_test": len(X_test),
            "mejor_modelo": mejor_nombre,
            "mejor_rmse": round(mejor_rmse, 2) if mejor_rmse != float("inf") else None,
            "resultados": resultados_modelos,
        })

    # Guardar best_model.json
    with open(BEST_MODEL_PATH, "w") as f:
        json.dump(best_models, f, indent=2)
    print(f"\n[COMPARADOR] best_model.json guardado con {len(best_models)} productos.")

    # Estadísticas globales
    from collections import Counter
    counter = Counter(best_models.values())
    print(f"\n[COMPARADOR] Resumen global:")
    for algo, count in counter.most_common():
        print(f"  {algo}: {count} productos")

    return {
        "modelos_evaluados": len(MODEL_REGISTRY),
        "total_productos": len(ranking_global),
        "productos_con_modelo": len(best_models),
        "resumen_algoritmos": dict(counter.most_common()),
        "detalle_por_producto": ranking_global,
    }


def cargar_mejor_modelo(producto_id: int):
    """Carga el mejor modelo guardado para un producto."""
    ruta = os.path.join(MODELS_DIR, f"best_{producto_id}.pkl")
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"No hay mejor modelo para producto_id={producto_id}")
    return joblib.load(ruta)


def obtener_mejor_algoritmo(producto_id: int) -> str:
    """Retorna el nombre del mejor algoritmo para un producto."""
    if os.path.exists(BEST_MODEL_PATH):
        with open(BEST_MODEL_PATH) as f:
            best = json.load(f)
        return best.get(str(producto_id), "Random Forest")
    return "Random Forest"


if __name__ == "__main__":
    resultado = entrenar_y_comparar_todos()
    print(f"\n[OK] Comparación completada. {resultado['productos_con_modelo']} productos con modelo.")
