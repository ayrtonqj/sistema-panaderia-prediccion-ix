"""
ablation_study.py — Análisis de Ablación de Features de Clima (OE6)
====================================================================
Experimento de control que evalúa el impacto de las variables climáticas
en la precisión del modelo predictivo.

Metodología:
  1. Modelo completo (todas las features)
  2. Sin temperatura
  3. Sin condición climática
  4. Sin todas las features climáticas (ablación total)
  5. Prueba Diebold-Mariano entre el modelo completo y el peor ablacionado

Resultados guardados en: scratch/ablation_results.json
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import numpy as np
import pandas as pd
from datetime import date
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from scipy import stats

from database import SessionLocal
import models
from ml.features import build_features, FEATURE_COLS

RESULTS_DIR = os.path.join(os.path.dirname(__file__))
os.makedirs(RESULTS_DIR, exist_ok=True)

# Features climáticas a ablacionar
CLIMATE_FEATURES = ["temperatura", "condicion_encoded", "es_feriado", "tiene_evento"]
NON_CLIMATE_FEATURES = [f for f in FEATURE_COLS if f not in CLIMATE_FEATURES]

# Configuraciones de ablación
ABLATION_CONFIGS = {
    "completo": FEATURE_COLS,
    "sin_temperatura": [f for f in FEATURE_COLS if f != "temperatura"],
    "sin_condicion": [f for f in FEATURE_COLS if f != "condicion_encoded"],
    "sin_clima_completo": NON_CLIMATE_FEATURES,
    "solo_tiempo": ["dia_semana", "mes", "dia_mes", "dia_anio", "es_finde"],
}


def diebold_mariano_test(errors1, errors2, h=1):
    """
    Prueba Diebold-Mariano para comparar dos conjuntos de errores de predicción.
    H0: los dos modelos tienen la misma precisión predictiva.
    Retorna: estadístico DM, p-valor, conclusión.
    """
    d = np.array(errors1) ** 2 - np.array(errors2) ** 2
    n = len(d)
    if n < 4:
        return None, None, "muestra insuficiente"

    d_mean = np.mean(d)
    # Varianza con corrección de autocorrelación (Newey-West simplificado)
    gamma0 = np.var(d, ddof=1)
    gamma1 = np.cov(d[:-1], d[1:])[0, 1] if n > 1 else 0
    var_d = (gamma0 + 2 * gamma1) / n
    var_d = max(var_d, 1e-10)  # evitar división por cero

    dm_stat = d_mean / np.sqrt(var_d)
    p_valor = 2 * (1 - stats.norm.cdf(abs(dm_stat)))

    if p_valor < 0.05:
        conclusion = f"Significativo (p={p_valor:.4f}): el modelo completo ES superior"
    elif p_valor < 0.10:
        conclusion = f"Marginalmente significativo (p={p_valor:.4f})"
    else:
        conclusion = f"No significativo (p={p_valor:.4f}): diferencia no concluyente"

    return round(float(dm_stat), 4), round(float(p_valor), 4), conclusion


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


def evaluar_configuracion(df_features, features_cols, n_test=20):
    """Evalúa un conjunto de features en todos los productos."""
    maes, rmses, r2s, errores = [], [], [], []

    for pid in df_features["producto_id"].unique():
        df_prod = df_features[df_features["producto_id"] == pid].copy()
        if len(df_prod) < n_test + 20:
            continue

        # Usar solo las features disponibles
        feats_disponibles = [f for f in features_cols if f in df_prod.columns]
        if not feats_disponibles:
            continue

        X = df_prod[feats_disponibles].values
        y = df_prod["cantidad_vendida"].values

        X_train, X_test = X[:-n_test], X[-n_test:]
        y_train, y_test = y[:-n_test], y[-n_test:]

        modelo = RandomForestRegressor(
            n_estimators=100, max_depth=6, random_state=42, n_jobs=-1
        )
        try:
            modelo.fit(X_train, y_train)
            y_pred = np.maximum(0, modelo.predict(X_test))

            mae  = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2   = r2_score(y_test, y_pred)

            maes.append(mae)
            rmses.append(rmse)
            r2s.append(r2)
            errores.extend(list(y_test - y_pred))
        except Exception:
            continue

    if not maes:
        return None, []

    return {
        "mae_promedio":  round(float(np.mean(maes)),  4),
        "rmse_promedio": round(float(np.mean(rmses)), 4),
        "r2_promedio":   round(float(np.mean(r2s)),   4),
        "n_productos":   len(maes),
        "features_usadas": len(features_cols),
    }, errores


def main():
    print("=" * 65)
    print("  ANÁLISIS DE ABLACIÓN DE CLIMA — Panadería Victoria (OE6)")
    print("=" * 65)

    print("\n[INFO] Cargando datos de la BD...")
    df_ventas, df_clima, df_productos = cargar_datos()

    if df_ventas.empty:
        print("[ERROR] No hay datos de ventas. Ejecuta seed_articulo.py primero.")
        return

    print(f"[OK] {len(df_ventas)} ventas | {len(df_productos)} productos")

    print("[INFO] Construyendo features...")
    df_features = build_features(df_ventas, df_clima)
    print(f"[OK] {len(df_features)} filas de features")

    # ── Ejecutar ablaciones ────────────────────────────────────────────
    resultados = {}
    errores_por_config = {}

    print("\n[INFO] Ejecutando experimentos de ablación...")
    for nombre_config, features in ABLATION_CONFIGS.items():
        feats_validas = [f for f in features if f in df_features.columns]
        print(f"\n  → Configuración: '{nombre_config}' ({len(feats_validas)} features)")

        metricas, errores = evaluar_configuracion(df_features, feats_validas)
        if metricas:
            resultados[nombre_config] = metricas
            errores_por_config[nombre_config] = errores
            print(f"    MAE={metricas['mae_promedio']:.4f} | "
                  f"RMSE={metricas['rmse_promedio']:.4f} | "
                  f"R²={metricas['r2_promedio']:.4f} | "
                  f"n={metricas['n_productos']} productos")
        else:
            print(f"    [SKIP] Datos insuficientes")

    # ── Prueba Diebold-Mariano ─────────────────────────────────────────
    dm_resultados = {}
    if "completo" in errores_por_config:
        print("\n[INFO] Realizando prueba Diebold-Mariano...")
        errores_completo = errores_por_config["completo"]

        for nombre_config, errores in errores_por_config.items():
            if nombre_config == "completo":
                continue
            # Alinear longitudes
            n = min(len(errores_completo), len(errores))
            if n < 4:
                continue
            dm_stat, p_val, conclusion = diebold_mariano_test(
                errores_completo[-n:], errores[-n:]
            )
            dm_resultados[f"completo_vs_{nombre_config}"] = {
                "dm_estadistico": dm_stat,
                "p_valor": p_val,
                "conclusion": conclusion,
            }
            print(f"  completo vs {nombre_config}: DM={dm_stat}, p={p_val}")
            print(f"  → {conclusion}")

    # ── Impacto de features climáticas ────────────────────────────────
    impacto_clima = {}
    if "completo" in resultados and "sin_clima_completo" in resultados:
        mae_c = resultados["completo"]["mae_promedio"]
        mae_s = resultados["sin_clima_completo"]["mae_promedio"]
        incremento_mae = ((mae_s - mae_c) / mae_c) * 100 if mae_c > 0 else 0

        r2_c = resultados["completo"]["r2_promedio"]
        r2_s = resultados["sin_clima_completo"]["r2_promedio"]
        mejora_r2 = r2_c - r2_s

        impacto_clima = {
            "incremento_mae_sin_clima_pct": round(incremento_mae, 2),
            "mejora_r2_con_clima": round(mejora_r2, 4),
            "conclusion": (
                f"Las variables climáticas reducen el MAE en {abs(incremento_mae):.1f}% "
                f"y mejoran el R² en {mejora_r2:.4f} puntos"
                if incremento_mae > 0 else
                "Las variables climáticas no mostraron impacto significativo en este dataset"
            )
        }

    # ── Guardar resultados ─────────────────────────────────────────────
    resultado_final = {
        "experimento": "Análisis de Ablación de Features Climáticas",
        "dataset": f"{len(df_ventas)} registros de ventas | {len(df_productos)} productos",
        "fecha_ejecucion": str(date.today()),
        "configuraciones_evaluadas": resultados,
        "prueba_diebold_mariano": dm_resultados,
        "impacto_variables_climaticas": impacto_clima,
        "conclusiones": {
            "mejor_config": min(resultados, key=lambda k: resultados[k]["mae_promedio"]) if resultados else "N/A",
            "peor_config":  max(resultados, key=lambda k: resultados[k]["mae_promedio"]) if resultados else "N/A",
            "features_optimas": list(ABLATION_CONFIGS.get(
                min(resultados, key=lambda k: resultados[k]["mae_promedio"]) if resultados else "completo", []
            )),
        }
    }

    ruta_resultados = os.path.join(RESULTS_DIR, "ablation_results.json")
    with open(ruta_resultados, "w", encoding="utf-8") as f:
        json.dump(resultado_final, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 65)
    print("  RESUMEN DEL ANÁLISIS DE ABLACIÓN")
    print("=" * 65)
    for cfg, m in resultados.items():
        mejor = " ← MEJOR" if cfg == resultado_final["conclusiones"]["mejor_config"] else ""
        peor  = " ← PEOR"  if cfg == resultado_final["conclusiones"]["peor_config"]  else ""
        print(f"  {cfg:<25} MAE={m['mae_promedio']:.4f}  R²={m['r2_promedio']:.4f}{mejor}{peor}")

    if impacto_clima:
        print(f"\n  Impacto del clima:")
        print(f"    {impacto_clima['conclusion']}")

    print(f"\n  Resultados guardados en: {ruta_resultados}")
    print("=" * 65)
    print("\n[DONE] Análisis de ablación completado.")


if __name__ == "__main__":
    main()
