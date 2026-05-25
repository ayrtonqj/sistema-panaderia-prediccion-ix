# Sistema Predictivo de Producción — Panadería Victoria

Sistema de predicción de demanda y automatización de cadena de suministro basado en Machine Learning para reducir mermas en una panadería.

## 📋 Descripción

Este proyecto implementa un sistema predictivo de producción que utiliza algoritmos de Machine Learning (Random Forest) para predecir la demanda diaria de productos de panadería, considerando variables climáticas, calendario de eventos y patrones históricos de ventas.

**Objetivo:** Reducir las mermas de producción en al menos 20% mediante predicciones precisas y automatización de la cadena de suministro.

### Características principales

- 🤖 **Modelo ML**: Random Forest Regressor con un modelo por producto
- 🌤️ **Integración climática**: API de Open-Meteo para Pacasmayo, Perú
- 📊 **Dashboard interactivo**: 8 páginas en Streamlit con visualización de KPIs
- 🔄 **Automatización**: n8n configurado con workflow de órdenes automáticas
- 📈 **Reportes financieros**: Exportación a PDF con gráficos

## 🛠️ Stack Tecnológico

| Componente | Tecnología |
|------------|-------------|
| Backend API | FastAPI + SQLAlchemy |
| Base de datos | PostgreSQL |
| ML | scikit-learn (Random Forest) |
| Frontend 1 (Analítico) | Streamlit + Plotly |
| Frontend 2 (Operativo) | Django + HTMX + Vanilla CSS |
| Visualización | Chart.js / Plotly |
| Automatización | n8n (preparado) |
| Contenedores | Docker Compose |

## 📁 Estructura del Proyecto

```
panaderia/
├── backend/
│   ├── main.py              # API FastAPI completa
│   ├── models.py           # Modelos SQLAlchemy
│   ├── database.py         # Conexión a PostgreSQL
│   └── ml/                 # Módulo de Machine Learning
│       ├── features.py     # Ingeniería de características
│       ├── trainer.py      # Entrenamiento del modelo
│       ├── predictor.py   # Generación de predicciones
│       ├── seed_data.py   # Datos sintéticos iniciales
│       ├── weather_api.py # Integración Open-Meteo
│       └── models_trained/ # Modelos .pkl entrenados
├── frontend/
│   ├── app.py              # Dashboard Streamlit analítico
│   └── pages/              # 8 páginas del dashboard
├── frontend2/              # Nuevo Dashboard Operativo
│   ├── manage.py           # Core Django
│   ├── core/               # Vistas (views.py) integradas con FastAPI
│   └── templates/          # Vistas HTML con HTMX y NProgress
├── docker-compose.yml      # Servicios: PostgreSQL, pgAdmin, n8n
├── n8n-workflow.json       # Workflow de n8n (órdenes automáticas)
├── setup_n8n_workflow.py   # Script para importar workflow en n8n
├── requirements.txt         # Dependencias Python
├── .env                    # Variables de entorno
└── AGENT.md               # Guía completa para desarrolladores
```

## 🚀 Instalación y Despliegue

### Prerequisites

- Python 3.14+
- Docker y Docker Compose
- PostgreSQL (opcional, puede usar Docker)

### 1. Clonar el repositorio

```bash
git clone <repositorio>
cd panaderia
```

### 2. Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto:

```env
DATABASE_URL=postgresql://eduardo:123456@localhost:5432/panaderia_victoria
```

### 3. Levantar servicios con Docker

```bash
docker-compose up -d
```

Esto iniciara:
- PostgreSQL (puerto 5432)
- pgAdmin (puerto 8080)
- n8n (puerto 5678)

### 4. Instalar dependencias Python

```bash
# Crear entorno virtual (recomendado)
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en Linux/Mac
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 5. Iniciar el backend (API FastAPI)

```bash
cd backend
uvicorn main:app --reload
```

La API estara disponible en: `http://localhost:8000`
Documentación Swagger: `http://localhost:8000/docs`

### 6. Iniciar el frontend 1 (Streamlit Analítico)

```bash
cd frontend
streamlit run app.py
```
El dashboard analítico estará disponible en: `http://localhost:8501`

### 7. Iniciar el frontend 2 (Django Operativo)

```bash
cd frontend2
python manage.py runserver 8001
```
El dashboard operativo (más rápido gracias a HTMX) estará disponible en: `http://localhost:8001`

### 8. Cargar datos iniciales (primera vez)

Desde la API o Swagger:
1. POST `/datos/semilla` — Carga 365 dias de datos historicos
2. POST `/ml/entrenar` — Entrena los modelos Random Forest
3. POST `/predicciones/generar?n_dias=7` — Genera predicciones

### 8. Configurar workflow de n8n (Automatizacion OE4)

El workflow de n8n automatiza la creacion de ordenes de compra cuando los insumos estan bajo stock minimo.

```bash
# Ejecutar script de configuracion automatica
python setup_n8n_workflow.py
```

Esto importara y activara el workflow que:
- Se ejecuta diariamente a las 8:00 AM
- Detecta insumos con stock bajo el minimo
- Crea ordenes de compra automaticas via la API
- Opcionalmente envia emails a proveedores

## 🔧 Configuración de servicios

### Credenciales por defecto

| Servicio | Credenciales |
|----------|---------------|
| PostgreSQL | `eduardo / 123456` |
| pgAdmin | `admin@tesis.com / admin` |
| n8n | `admin / admin123` |

### URLs de servicios

| Servicio | URL |
|----------|-----|
| API FastAPI | http://localhost:8000 |
| Documentación API | http://localhost:8000/docs |
| Dashboard Django | http://localhost:8001 |
| Dashboard Streamlit | http://localhost:8501 |
| pgAdmin | http://localhost:8080 |
| n8n (Workflows) | http://localhost:5678 |

### Automatización con n8n (OE4)

El sistema incluye un workflow de n8n configurado para automatizar la cadena de suministro:

**Funcionamiento:**
- **Trigger:** Cada día a las 8:00 AM
- **Detección:** Consulta `/insumos/alertas/` para identificar insumos bajo stock mínimo
- **Acción:** Crea órdenes de compra automáticas via `POST /ordenes-compra/`
- **Notificación:** Envía email al proveedor (si tiene email configurado)

**Archivos:**
- `n8n-workflow.json` — Definición del workflow
- `setup_n8n_workflow.py` — Script para importar y activar el workflow

**Para activar:**
```bash
python setup_n8n_workflow.py
```

## 📊 Uso del Sistema

### Cargar datos historicos

```bash
curl -X POST http://localhost:8000/datos/semilla
```

### Entrenar modelos

```bash
curl -X POST http://localhost:8000/ml/entrenar
```

### Generar predicciones

```bash
curl -X POST "http://localhost:8000/predicciones/generar?n_dias=7"
```

### Sincronizar clima (Open-Meteo)

```bash
curl -X POST "http://localhost:8000/clima/sincronizar?dias=7"
```

## 📈 Endpoints principales

| Endpoint | Descripcion |
|----------|-------------|
| `GET /dashboard/resumen` | KPIs generales del sistema |
| `GET /mermas/analisis` | Analisis de mermas por motivo/producto |
| `GET /predicciones/vs-real` | Comparacion prediccion vs realidad |
| `GET /insumos/alertas/` | Insumos bajo stock minimo |
| `GET /sistema/estado` | Estado completo del sistema |

## 🧪 Testing

Para verificar que todo funciona:

1. Verificar estado del sistema:
```bash
curl http://localhost:8000/sistema/estado
```

2. Verificar que el dashboard carga:
Abrir `http://localhost:8501` en el navegador

## 📝 Variables de entorno

El archivo `.env` debe contener:

```env
# Base de datos PostgreSQL
DATABASE_URL=postgresql://eduardo:123456@localhost:5432/panaderia_victoria
```

## 🔄 Scripts de utilidad

- `backend/reset_db.py` — Resetear la base de datos
- `backend/ml/seed_data.py` — Regenerar datos sinteticos

## 📦 Dependencias principales

```
fastapi
uvicorn
sqlalchemy
psycopg2-binary
pandas
numpy
scikit-learn
joblib
streamlit
plotly
xhtml2pdf
httpx
```

## 🤝 Contribuciones

Este proyecto es parte de una tesis de investigacion. Para consultas o contribuciones, contactar al equipo de desarrollo.

## 📄 Licencia

Para uso academico — Universidad Nacional de Trujillo (UNT) 2026-I

## 📅 Historial de versiones

- v2.0 (Abril 2026) — Sistema completo con 8 paginas de dashboard
- v1.0 (2025) — Prototipo inicial con API basica

---

*Sistema desarrollado para la Tesis de Ingenieria — Universidad Nacional de Trujillo (UNT) 2026-I*