"""
weather_api.py — Integración con Open-Meteo API (Gratuita, sin Key)
Obtiene el pronóstico real para Pacasmayo, Perú.
Coordenadas Pacasmayo: Lat -7.4006, Lon -79.5714

Optimizaciones: cache en memoria con TTL de 3 horas.
"""
import httpx
import pandas as pd
from datetime import date, timedelta, datetime

LAT = -7.4006
LON = -79.5714

_cache_pronostico = None
_cache_timestamp = None
CACHE_TTL_HORAS = 3


def invalidar_cache_clima():
    global _cache_pronostico, _cache_timestamp
    _cache_pronostico = None
    _cache_timestamp = None


async def obtener_pronostico_pacasmayo(dias: int = 7):
    global _cache_pronostico, _cache_timestamp

    if _cache_pronostico is not None and _cache_timestamp is not None:
        if (datetime.now() - _cache_timestamp).total_seconds() < CACHE_TTL_HORAS * 3600:
            return _cache_pronostico[:min(dias, len(_cache_pronostico))]

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "daily": ["temperature_2m_max", "temperature_2m_min", "weathercode"],
        "timezone": "auto",
        "forecast_days": max(dias, 7)
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            daily = data["daily"]
            pronosticos = []

            for i in range(len(daily["time"])):
                fecha_str = daily["time"][i]
                t_max = daily["temperature_2m_max"][i]
                t_min = daily["temperature_2m_min"][i]
                code = daily["weathercode"][i]

                condicion = "Soleado"
                if code in [1, 2, 3]: condicion = "Parcialmente nublado"
                elif code in [45, 48]: condicion = "Nublado"
                elif code >= 51: condicion = "Lluvia"

                pronosticos.append({
                    "fecha": date.fromisoformat(fecha_str),
                    "temperatura_promedio": round((t_max + t_min) / 2, 1),
                    "condicion": condicion
                })

            _cache_pronostico = pronosticos
            _cache_timestamp = datetime.now()

            return pronosticos[:dias]

        except Exception as e:
            print(f"[ERROR] No se pudo obtener clima de Open-Meteo: {e}")
            return []


if __name__ == "__main__":
    import asyncio
    res = asyncio.run(obtener_pronostico_pacasmayo())
    print(res)
