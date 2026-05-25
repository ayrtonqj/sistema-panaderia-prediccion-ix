import requests

try:
    r = requests.get("http://localhost:8000/predicciones/vs-real?dias=30")
    data = r.json()
    print("--- RESPUESTA DEL BACKEND ---")
    print(f"Status Code: {r.status_code}")
    print(f"MAE Global: {data.get('mae_global')}")
    if data.get('detalle'):
        print(f"Primer registro: {data['detalle'][0]}")
        print(f"Columnas disponibles: {list(data['detalle'][0].keys())}")
    else:
        print("Detalle está vacío")
except Exception as e:
    print(f"Error al conectar: {e}")
