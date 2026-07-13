"""
features.py — Ingenieria de caracteristicas para modelos predictivos.
Genera features temporales, climaticas y de ventas historicas para:
  - Entrenamiento (con target)
  - Prediccion futura (sin target, con propagacion iterativa)
"""

import numpy as np
import pandas as pd

FEATURE_COLS = [
    "dia_semana", "mes", "dia_mes", "dia_anio", "es_finde",
    "es_feriado", "tiene_evento", "temperatura", "condicion_encoded",
    "ventas_lag_1", "ventas_lag_7",
    "ventas_rolling_7", "ventas_rolling_30",
]

CONDICION_MAP = {
    "Soleado": 0, "Parcialmente nublado": 1, "Nublado": 2,
    "Lluvia ligera": 3, "Lluvia": 4,
}


def _build_row(fecha, row_clima, ventas_recientes, producto_id):
    arr = np.array(ventas_recientes)
    lag1 = arr[-1] if len(arr) >= 1 else 0
    lag7 = arr[-7] if len(arr) >= 7 else lag1
    rolling7 = np.mean(arr[-7:]) if len(arr) >= 7 else lag1
    rolling30 = np.mean(arr[-30:]) if len(arr) >= 30 else lag1
    return {
        "dia_semana": fecha.dayofweek,
        "mes": fecha.month,
        "dia_mes": fecha.day,
        "dia_anio": fecha.dayofyear,
        "es_finde": int(fecha.dayofweek in [5, 6]),
        "es_feriado": int(row_clima.get("es_feriado", False)),
        "tiene_evento": int(bool(row_clima.get("evento_especial"))),
        "temperatura": row_clima.get("temperatura_promedio", 20.0),
        "condicion_encoded": CONDICION_MAP.get(row_clima.get("condicion", ""), 1),
        "ventas_lag_1": lag1,
        "ventas_lag_7": lag7,
        "ventas_rolling_7": rolling7,
        "ventas_rolling_30": rolling30,
        "fecha": fecha,
        "producto_id": producto_id,
    }


def build_features(df_hist, df_clima):
    rows = []
    for producto_id in df_hist["producto_id"].unique():
        prod_hist = df_hist[df_hist["producto_id"] == producto_id].sort_values("fecha")
        ventas_recientes = []
        for _, row in prod_hist.iterrows():
            fecha = pd.to_datetime(row["fecha"])
            clima_row = df_clima[df_clima["fecha"] == fecha]
            row_clima = clima_row.iloc[0].to_dict() if not clima_row.empty else {}
            feat = _build_row(fecha, row_clima, ventas_recientes, producto_id)
            feat["cantidad_vendida"] = row["cantidad_vendida"]
            rows.append(feat)
            ventas_recientes.append(row["cantidad_vendida"])
            ventas_recientes = ventas_recientes[-60:]
    return pd.DataFrame(rows)


def get_X_y(df):
    """Separa features (X) y target (y) de un DataFrame de features."""
    return df[FEATURE_COLS].values, df["cantidad_vendida"].values


def build_future_features(df_hist, df_clima_futuro, producto_id, n_days=7, predicted_values=None):
    hist = df_hist[df_hist["producto_id"] == producto_id].copy()
    hist = hist.sort_values("fecha").tail(30)
    ventas_recientes = list(hist["cantidad_vendida"].values)
    rows = []
    for i, (_, row_clima) in enumerate(df_clima_futuro.iterrows()):
        fecha = pd.to_datetime(row_clima["fecha"])
        if predicted_values:
            ventanas_con_pred = list(ventas_recientes) + list(predicted_values[:i])
        else:
            ventanas_con_pred = ventas_recientes + [ventas_recientes[-1]] * i if ventas_recientes else [0] * i
        feat = _build_row(fecha, row_clima, ventanas_con_pred, producto_id)
        rows.append(feat)
    return pd.DataFrame(rows)
