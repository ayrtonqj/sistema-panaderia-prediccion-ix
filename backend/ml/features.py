"""
features.py — Ingeniería de características para el modelo predictivo
Construye el DataFrame de entrenamiento a partir de ventas + clima.
Variables usadas por el Random Forest:
  - Temporales: dia_semana, mes, dia_mes, dia_anio
  - Contextuales: es_feriado, temperatura, condicion_encoded
  - Lags: ventas_lag_1, ventas_lag_7 (ventas del día anterior y de hace 7 días)
  - Ventana móvil: ventas_rolling_7 (promedio últimos 7 días)
"""
import pandas as pd
import numpy as np


CONDICION_MAP = {
    "Soleado": 0,
    "Parcialmente nublado": 1,
    "Nublado": 2,
    "Lluvia ligera": 3,
    "Lluvia": 4,
}


def build_features(df_ventas: pd.DataFrame, df_clima: pd.DataFrame) -> pd.DataFrame:
    """
    Construye el DataFrame de features listo para entrenar el modelo.

    Parámetros:
        df_ventas: DataFrame con columnas [producto_id, fecha, cantidad_vendida]
        df_clima:  DataFrame con columnas [fecha, temperatura_promedio, condicion,
                                           es_feriado, evento_especial]

    Retorna:
        DataFrame con features por (producto_id, fecha) y columna target 'cantidad_vendida'
    """
    # Normalizar tipos de fecha
    df_ventas = df_ventas.copy()
    df_clima = df_clima.copy()
    df_ventas["fecha"] = pd.to_datetime(df_ventas["fecha"])
    df_clima["fecha"] = pd.to_datetime(df_clima["fecha"])

    # Merge ventas + clima por fecha
    df = df_ventas.merge(df_clima, on="fecha", how="left")

    # ── Variables temporales ──────────────────────────────────────
    df["dia_semana"] = df["fecha"].dt.dayofweek        # 0=Lunes, 6=Domingo
    df["mes"] = df["fecha"].dt.month
    df["dia_mes"] = df["fecha"].dt.day
    df["dia_anio"] = df["fecha"].dt.dayofyear
    # Fin de semana: sábado=5, domingo=6 → ventas significativamente mayores
    df["es_finde"] = df["dia_semana"].isin([5, 6]).astype(int)

    # ── Variables contextuales ─────────────────────────────────────
    df["es_feriado"] = df["es_feriado"].fillna(False).astype(int)
    df["tiene_evento"] = df["evento_especial"].notna().astype(int)
    df["temperatura"] = df["temperatura_promedio"].fillna(df["temperatura_promedio"].median())
    df["condicion_encoded"] = (
        df["condicion"].map(CONDICION_MAP).fillna(1)  # default: Parcialmente nublado
    )

    # ── Lags y ventanas móviles por producto ──────────────────────
    df = df.sort_values(["producto_id", "fecha"]).reset_index(drop=True)

    df["ventas_lag_1"] = df.groupby("producto_id")["cantidad_vendida"].shift(1)
    df["ventas_lag_7"] = df.groupby("producto_id")["cantidad_vendida"].shift(7)
    df["ventas_rolling_7"] = (
        df.groupby("producto_id")["cantidad_vendida"]
        .transform(lambda x: x.shift(1).rolling(7, min_periods=1).mean())
    )
    df["ventas_rolling_30"] = (
        df.groupby("producto_id")["cantidad_vendida"]
        .transform(lambda x: x.shift(1).rolling(30, min_periods=7).mean())
    )

    # Eliminar filas sin suficientes datos históricos
    df = df.dropna(subset=["ventas_lag_1", "ventas_lag_7"])

    return df


FEATURE_COLS = [
    "dia_semana", "mes", "dia_mes", "dia_anio",
    "es_finde", "es_feriado", "tiene_evento",
    "temperatura", "condicion_encoded",
    "ventas_lag_1", "ventas_lag_7",
    "ventas_rolling_7", "ventas_rolling_30",
]

TARGET_COL = "cantidad_vendida"


def get_X_y(df: pd.DataFrame):
    """Separa features y target del DataFrame construido por build_features."""
    X = df[FEATURE_COLS].values
    y = df[TARGET_COL].values
    return X, y


def build_future_features(
    df_hist: pd.DataFrame,
    df_clima_futuro: pd.DataFrame,
    producto_id: int,
    n_days: int = 7,
) -> pd.DataFrame:
    """
    Construye features para los próximos n_days días (sin target).
    Usa los últimos 30 días de historia para calcular lags y rolling.
    """
    hist = df_hist[df_hist["producto_id"] == producto_id].copy()
    hist = hist.sort_values("fecha").tail(30)

    rows = []
    for i, row in df_clima_futuro.iterrows():
        fecha = pd.to_datetime(row["fecha"])
        # Lags sobre datos ya predichos iterativamente
        ventas_recientes = hist["cantidad_vendida"].values
        lag1 = ventas_recientes[-1] if len(ventas_recientes) >= 1 else 0
        lag7 = ventas_recientes[-7] if len(ventas_recientes) >= 7 else lag1
        rolling7 = np.mean(ventas_recientes[-7:]) if len(ventas_recientes) >= 1 else lag1
        rolling30 = np.mean(ventas_recientes[-30:]) if len(ventas_recientes) >= 1 else lag1

        rows.append({
            "dia_semana": fecha.dayofweek,
            "mes": fecha.month,
            "dia_mes": fecha.day,
            "dia_anio": fecha.dayofyear,
            "es_finde": int(fecha.dayofweek in [5, 6]),
            "es_feriado": int(row.get("es_feriado", False)),
            "tiene_evento": int(bool(row.get("evento_especial"))),
            "temperatura": row.get("temperatura_promedio", 20.0),
            "condicion_encoded": CONDICION_MAP.get(row.get("condicion", ""), 1),
            "ventas_lag_1": lag1,
            "ventas_lag_7": lag7,
            "ventas_rolling_7": rolling7,
            "ventas_rolling_30": rolling30,
            "fecha": fecha,
            "producto_id": producto_id,
        })

        # Agregar predicción iterativa a la historia temporal
        hist = pd.concat([
            hist,
            pd.DataFrame([{"producto_id": producto_id, "fecha": fecha, "cantidad_vendida": lag1}])
        ], ignore_index=True)

    return pd.DataFrame(rows)
