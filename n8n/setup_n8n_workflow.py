"""
Script para importar automaticamente el workflow de n8n en el sistema Panaderia Victoria.

Este script:
1. Verifica que n8n este corriendo en localhost:5678
2. Importa el workflow JSON via la API de n8n
3. Activa el workflow para ejecuciones automaticas

Uso:
    python setup_n8n_workflow.py

Requisitos:
    - n8n corriendo en Docker (docker-compose up -d)
    - Backend FastAPI corriendo en localhost:8000
    - API Key de n8n (se genera desde la interfaz de n8n)
"""

import json
import time
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("[ERROR] requests no instalado. Ejecutar: pip install requests")
    sys.exit(1)

# Configuracion
N8N_BASE_URL = "http://localhost:5678"
BACKEND_URL = "http://localhost:8000"
WORKFLOW_FILE = Path(__file__).parent / "n8n-workflow.json"


def obtener_api_key():
    """Solicita al usuario la API Key de n8n."""
    print("\n" + "=" * 60)
    print("NECESITAS UNA API KEY DE N8N")
    print("=" * 60)
    print("\nPara obtener tu API Key:")
    print("  1. Abre http://localhost:5678 en tu navegador")
    print("  2. Inicia sesion con: admin / admin123")
    print("  3. Haz click en tu avatar (esquina inferior izquierda)")
    print("  4. Selecciona 'Settings' > 'API Keys'")
    print("  5. Haz click en 'Create API Key'")
    print("  6. Copia la clave generada")
    print("=" * 60)

    api_key = input("\nIngresa tu API Key de n8n: ").strip()

    if not api_key:
        print("[ERROR] API Key no proporcionada. Abortando.")
        sys.exit(1)

    return api_key


def verificar_servicios(api_key):
    """Verifica que n8n y el backend esten corriendo."""
    print("\n[1/4] Verificando servicios...")

    # Verificar backend
    try:
        resp = requests.get(f"{BACKEND_URL}/", timeout=5)
        if resp.status_code == 200:
            print("  [OK] Backend FastAPI esta corriendo")
        else:
            print(f"  [WARN] Backend respondio con status {resp.status_code}")
    except requests.exceptions.ConnectionError:
        print("  [ERROR] Backend no esta corriendo en http://localhost:8000")
        print("  -> Iniciar con: cd backend && uvicorn main:app --reload")
        return False

    # Verificar n8n con API Key
    max_retries = 3
    headers = {"X-N8N-API-KEY": api_key}

    for i in range(max_retries):
        try:
            resp = requests.get(f"{N8N_BASE_URL}/healthz", timeout=5, headers=headers)
            if resp.status_code == 200:
                print("  [OK] n8n esta corriendo y saludable")
                return True
            elif resp.status_code == 401:
                print("  [ERROR] API Key invalida o no autorizada")
                return False
            else:
                print(f"  [WARN] n8n respondio con status {resp.status_code}, reintentando...")
        except requests.exceptions.ConnectionError:
            if i < max_retries - 1:
                print(f"  [WARN] n8n no responde, reintentando ({i+1}/{max_retries})...")
                time.sleep(5)
            else:
                print("  [ERROR] n8n no esta corriendo en http://localhost:5678")
                print("  -> Iniciar con: docker-compose up -d")
                return False

    return False


def verificar_datos_api():
    """Verifica que la API tenga datos de insumos y proveedores."""
    print("\n[2/4] Verificando datos en la API...")

    try:
        # Verificar insumos
        resp = requests.get(f"{BACKEND_URL}/insumos/", timeout=5)
        if resp.status_code == 200:
            insumos = resp.json()
            print(f"  [OK] {len(insumos)} insumos encontrados")
        else:
            print("  [WARN] No se pudieron obtener insumos")

        # Verificar proveedores
        resp = requests.get(f"{BACKEND_URL}/proveedores/", timeout=5)
        if resp.status_code == 200:
            proveedores = resp.json()
            print(f"  [OK] {len(proveedores)} proveedores encontrados")
        else:
            print("  [WARN] No se pudieron obtener proveedores")

        # Verificar alertas
        resp = requests.get(f"{BACKEND_URL}/insumos/alertas/", timeout=5)
        if resp.status_code == 200:
            alertas = resp.json()
            criticos = [a for a in alertas if a.get("necesita_reorden")]
            print(f"  [OK] {len(criticos)} insumos bajo stock minimo")
            if criticos:
                print("  -> Estos insumos generaran ordenes automaticas:")
                for a in criticos:
                    print(f"     - {a['nombre']}: {a['stock_actual']} {a['unidad_medida']} (min: {a['stock_minimo']})")

        return True
    except Exception as e:
        print(f"  [ERROR] Error verificando datos: {e}")
        return False


def importar_workflow(api_key):
    """Importa el workflow JSON en n8n via API."""
    print("\n[3/4] Importando workflow en n8n...")

    if not WORKFLOW_FILE.exists():
        print(f"  [ERROR] Archivo de workflow no encontrado: {WORKFLOW_FILE}")
        return False

    with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
        workflow_data = json.load(f)

    # Preparar payload (sin 'active' porque es read-only al crear)
    payload = {
        "name": workflow_data["name"],
        "nodes": workflow_data["nodes"],
        "connections": workflow_data["connections"],
        "settings": workflow_data.get("settings", {}),
    }

    headers = {
        "X-N8N-API-KEY": api_key,
        "Content-Type": "application/json",
    }

    try:
        # Crear workflow via API (sin active=True)
        resp = requests.post(
            f"{N8N_BASE_URL}/api/v1/workflows",
            json=payload,
            headers=headers,
            timeout=10,
        )

        if resp.status_code in [200, 201]:
            result = resp.json()
            workflow_id = result.get("data", result).get("id") or result.get("id")
            if not workflow_id:
                print(f"  [WARN] No se pudo obtener el ID del workflow")
                print(f"  -> Respuesta: {json.dumps(result, indent=2)}")
                return True

            print(f"  [OK] Workflow creado (ID: {workflow_id})")

            # Ahora activar el workflow separadamente
            print("  -> Activando workflow...")
            activate_resp = requests.patch(
                f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}",
                json={"active": True},
                headers=headers,
                timeout=10,
            )

            if activate_resp.status_code in [200, 201]:
                print(f"  [OK] Workflow activado exitosamente!")
                return True
            else:
                print(f"  [WARN] No se pudo activar automaticamente: {activate_resp.status_code}")
                print(f"  -> Tendras que activarlo manualmente desde la interfaz de n8n")
                return True

        elif resp.status_code == 401:
            print("  [ERROR] API Key invalida")
            return False
        else:
            print(f"  [ERROR] Error importando workflow: {resp.status_code}")
            print(f"  -> Respuesta: {resp.text}")
            return False

    except Exception as e:
        print(f"  [ERROR] Excepcion importando workflow: {e}")
        return False


def verificar_activacion(api_key):
    """Verifica que el workflow este activo y funcionando."""
    print("\n[4/4] Verificando activacion del workflow...")

    headers = {"X-N8N-API-KEY": api_key}

    try:
        # Listar workflows activos
        resp = requests.get(
            f"{N8N_BASE_URL}/api/v1/workflows",
            headers=headers,
            timeout=10,
        )

        if resp.status_code == 200:
            workflows = resp.json().get("data", [])
            workflow_encontrado = None

            for wf in workflows:
                if "Panaderia Victoria" in wf.get("name", ""):
                    workflow_encontrado = wf
                    break

            if workflow_encontrado:
                print("  [OK] Workflow encontrado en n8n!")
                print(f"  -> Nombre: {workflow_encontrado['name']}")
                print(f"  -> Activo: {workflow_encontrado.get('active', False)}")
                print(f"  -> URL para editar: {N8N_BASE_URL}/workflow/{workflow_encontrado['id']}")
                return True
            else:
                print("  [WARN] Workflow no encontrado en la lista")
                return False
        else:
            print(f"  [ERROR] Error listando workflows: {resp.status_code}")
            return False

    except Exception as e:
        print(f"  [ERROR] Excepcion verificando activacion: {e}")
        return False


def imprimir_instrucciones():
    """Imprime instrucciones de uso y configuracion."""
    print("\n" + "=" * 60)
    print("WORKFLOW DE N8N CONFIGURADO EXITOSAMENTE")
    print("=" * 60)
    print("\nEl workflow 'Panaderia Victoria - Ordenes Automaticas de Compra'")
    print("ha sido importado y activado en n8n.")
    print("\nComo funciona:")
    print("  1. Se ejecuta automaticamente cada dia a las 8:00 AM")
    print("  2. Consulta la API para verificar insumos bajo stock minimo")
    print("  3. Para cada insumo critico:")
    print("     - Calcula la cantidad a ordenar (2x stock minimo - stock actual)")
    print("     - Obtiene datos del proveedor asignado")
    print("     - Crea una orden de compra automatica via POST /ordenes-compra/")
    print("     - Envia email al proveedor (si tiene email configurado)")
    print("  4. Genera un resumen de ordenes creadas")
    print("\nUrls utiles:")
    print(f"  - Editar workflow: {N8N_BASE_URL}")
    print(f"  - Ver ordenes creadas: http://localhost:8501 (Streamlit > Ordenes de Compra)")
    print(f"  - API de insumos: {BACKEND_URL}/insumos/alertas/")
    print("\nPara ejecutar manualmente:")
    print("  1. Abrir http://localhost:5678 en el navegador")
    print("  2. Ir al workflow 'Panaderia Victoria - Ordenes Automaticas de Compra'")
    print("  3. Click en 'Execute Workflow'")
    print("\nPara desactivar el workflow:")
    print("  1. Abrir el workflow en n8n")
    print("  2. Toggle 'Active' a OFF")
    print("=" * 60)


def main():
    """Funcion principal."""
    print("\n" + "=" * 60)
    print("SETUP DE N8N - PANADERIA VICTORIA")
    print("=" * 60)

    # Obtener API Key
    api_key = obtener_api_key()

    # Paso 1: Verificar servicios
    if not verificar_servicios(api_key):
        print("\n[ERROR] Servicios no disponibles. Abortando setup.")
        sys.exit(1)

    # Paso 2: Verificar datos
    if not verificar_datos_api():
        print("\n[WARN] Algunos datos pueden faltar, continuando...")

    # Paso 3: Importar workflow
    if not importar_workflow(api_key):
        print("\n[ERROR] No se pudo importar el workflow. Abortando setup.")
        sys.exit(1)

    # Paso 4: Verificar activacion
    verificar_activacion(api_key)

    # Imprimir instrucciones
    imprimir_instrucciones()

    print("\n[OK] Setup completado exitosamente!\n")


if __name__ == "__main__":
    main()
