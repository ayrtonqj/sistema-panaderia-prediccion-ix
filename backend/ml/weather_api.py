"""
weather_api.py — Integración con Open-Meteo API (Gratuita, sin Key)
Obtiene el pronóstico real para Pacasmayo, Perú.
Coordenadas Pacasmayo: Lat -7.4006, Lon -79.5714
"""
import httpx
import pandas as pd
from datetime import date, timedelta

# Coordenadas de Pacasmayo
LAT = -7.4006
LON = -79.5714

async def obtener_pronostico_pacasmayo(dias: int = 7):
    """
    Consulta la API de Open-Meteo para obtener el pronóstico del clima.
    Retorna una lista de diccionarios listos para la BD.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "daily": ["temperature_2m_max", "temperature_2m_min", "weathercode"],
        "timezone": "auto",
        "forecast_days": dias
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

                # Mapeo de códigos WMO a nuestras categorías
                # 0=Despejado, 1-3=Nubosidad, 45-48=Niebla, 51-67=Lluvia
                condicion = "Soleado"
                if code in [1, 2, 3]: condicion = "Parcialmente nublado"
                elif code in [45, 48]: condicion = "Nublado"
                elif code >= 51: condicion = "Lluvia"

                pronosticos.append({
                    "fecha": date.fromisoformat(fecha_str),
                    "temperatura_promedio": round((t_max + t_min) / 2, 1),
                    "condicion": condicion
                })
            
            return pronosticos

        except Exception as e:
            print(f"[ERROR] No se pudo obtener clima de Open-Meteo: {e}")
            # Fallback: retornar promedios básicos si falla la API
            return []

if __name__ == "__main__":
    import asyncio
    res = asyncio.run(obtener_pronostico_pacasmayo())
    print(res)
