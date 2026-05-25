# AGENT.md — Sistema Predictivo Panadería Victoria

Guía de contexto completo para agentes de IA que trabajen en este proyecto.
Leer este archivo **primero** antes de cualquier tarea de desarrollo.

---

## 1. Descripción del proyecto

**Nombre:** Sistema Predictivo de Producción y Automatización de Cadena de Suministro — Panadería Victoria

**Institución:** Universidad Nacional de Trujillo (UNT) — Tesis de Ingeniería 2026-I

**Objetivo académico:** Reducir las mermas de producción en la Panadería Victoria de Pacasmayo en **≥ 20%** mediante un sistema basado en Machine Learning y Business Intelligence.

**Hipótesis:** La implementación de un sistema predictivo de producción y automatización de la cadena de suministro basado en inteligencia artificial y herramientas de Business Intelligence reduce significativamente las mermas de producción en la Panadería Victoria, en un porcentaje no menor al 20% respecto al nivel de merma actual, con un nivel de confianza del 95%.

**Limitaciones del estudio:**
- **Técnico:** La precisión del modelo depende de la disponibilidad y calidad de datos históricos; puede requerirse período de depuración.
- **Económico:** Presupuesto limitado a infraestructura local; uso de herramientas de código abierto mitiga este factor.
- **Operativo:** Adopción requiere capacitación y período de adaptación; posible resistencia al cambio.

**Stack tecnológico:**
- **Backend API:** FastAPI + SQLAlchemy + PostgreSQL
- **ML:** scikit-learn (Random Forest Regressor), un modelo por producto
- **Frontend Analítico:** Streamlit (dashboard interactivo con 8 páginas)
- **Frontend Operativo:** Django + HTMX + Vanilla CSS (port 8001)
- **Automatización:** n8n (flujos de órdenes de compra automáticas)
- **Infraestructura:** Docker Compose (PostgreSQL + pgAdmin + n8n)
- **ORM:** SQLAlchemy 2.x con `from_attributes = True`
- **Python:** 3.14 (Windows, PowerShell)

---

## 2. Estructura del proyecto

```
d:\.UNT\2026-I\TESIS I\panaderia\
│
├── AGENT.md                        ← Este archivo (guía completa del sistema)
├── tesis.md                        ← Objetivos y problema de investigación
├── .env                            ← Credenciales BD (NO commitear)
├── docker-compose.yml              ← PostgreSQL + pgAdmin + n8n
├── requirements.txt                ← Dependencias Python
├── n8n-workflow.json               ← Workflow de n8n (órdenes automáticas)
├── setup_n8n_workflow.py           ← Script para importar workflow en n8n
│
├── backend/
│   ├── main.py                     ← API FastAPI completa (847 líneas)
│   ├── models.py                   ← Modelos SQLAlchemy (9 tablas)
│   ├── database.py                 ← Conexión BD (lee .env)
│   ├── reset_db.py                 ← Script para resetear BD
│   │
│   └── ml/
│       ├── __init__.py
│       ├── features.py             ← Ingeniería de características (13 features)
│       ├── seed_data.py            ← Generador de datos históricos sintéticos
│       ├── trainer.py              ← Entrenamiento Random Forest
│       ├── predictor.py            ← Generación de predicciones
│       ├── weather_api.py          ← Integración Open-Meteo (sin API key)
│       └── models_trained/
│           ├── 1.pkl               ← Pan Frances
│           ├── 1_meta.json         ← Métricas del modelo
│           ├── 2.pkl               ← Pan Integral
│           ├── 2_meta.json
│           ├── 3.pkl               ← Pan de Molde
│           ├── 3_meta.json
│           ├── 4.pkl               ← Croissant
│           ├── 4_meta.json
│           ├── 5.pkl               ← Empanada de Carne
│           ├── 5_meta.json
│           ├── 6.pkl               ← Torta de Cumpleaños
│           ├── 6_meta.json
│           ├── 7.pkl               ← Galletas de Avena
│           └── 7_meta.json
│
├── frontend/
│   ├── app.py                      ← Dashboard Streamlit principal (35 líneas)
│   └── pages/
│       ├── Resumen.py               ← Dashboard KPIs principal
│       ├── Registro_Diario.py      ← Registro de ventas y mermas (206 líneas)
│       ├── Predicciones.py         ← Visualización de predicciones ML (140 líneas)
│       ├── Analisis_Mermas.py      ← Análisis Pareto de mermas (116 líneas)
│       ├── Inventario.py           ← Gestión de stock de insumos (106 líneas)
│       ├── Ordenes_Compra.py        ← Gestión de órdenes de reposición (122 líneas)
│       ├── Reportes_Financieros.py ← Reportes financieros + PDF (261 líneas)
│       └── Modelo_Estadistico.py   ← Métricas del modelo ML (177 líneas)
│
├── frontend2/                      ← Dashboard Operativo en Django (Port 8001)
│   ├── manage.py                   ← Entrypoint de Django
│   ├── core/                       ← App de Django con views.py que consume a FastAPI
│   └── templates/core/             ← Vistas HTML5 + Vanilla CSS + HTMX para SPA
│
├── venv/                           ← Entorno virtual Python
└── docs/                           ← Documentación adicional
```

---

## 3. Servicios en ejecución

| Servicio | URL | Credenciales |
|---|---|---|
| **FastAPI** (backend) | `http://localhost:8000` | — |
| **FastAPI Docs** | `http://localhost:8000/docs` | — |
| **Django** (frontend operativo) | `http://localhost:8001` | — |
| **Streamlit** (frontend analítico) | `http://localhost:8501` | — |
| **PostgreSQL** | `localhost:5432` | `eduardo / 123456` |
| **pgAdmin** | `http://localhost:8080` | `admin@tesis.com / admin` |
| **n8n** | `http://localhost:5678` | `admin / admin123` |

### Comandos para iniciar

```powershell
# Desde d:\.UNT\2026-I\TESIS I\panaderia\

# Infraestructura Docker
docker-compose up -d

# Backend (abrir terminal en backend/)
cd backend
uvicorn main:app --reload

# Frontend 1: Streamlit (abrir terminal en frontend/)
cd frontend
streamlit run app.py

# Frontend 2: Django (abrir terminal en frontend2/)
cd frontend2
python manage.py runserver 8001
```

> **IMPORTANTE:** Uvicorn debe ejecutarse desde `backend/`, no desde la raíz del proyecto, porque `main.py` importa `models` y `database` con rutas relativas.

---

## 4. Base de datos — Schema PostgreSQL

**Base de datos:** `panaderia_victoria`

### Tablas dimensionales (contexto)

| Tabla | Descripción | Campos clave |
|---|---|---|
| `dim_productos` | Catálogo de productos | `id, nombre, categoria, precio, costo` |
| `dim_clima` | Variables climáticas diarias | `fecha (PK), temperatura_promedio, condicion, es_feriado, evento_especial` |
| `dim_proveedores` | Catálogo de proveedores | `id, nombre, contacto, telefono, email` |
| `insumos_criticos` | Stock de insumos | `id, nombre, stock_actual, stock_minimo, unidad_medida, proveedor_id` |
| `fichas_tecnicas` | Recetas (insumo por producto) | `id, producto_id, insumo_id, cantidad_necesaria` |

### Tablas de hechos (transacciones)

| Tabla | Descripción | Campos clave |
|---|---|---|
| `fact_ventas` | Ventas diarias por producto | `id, producto_id, fecha, cantidad_vendida, cantidad_producida, created_at` |
| `fact_mermas` | Mermas diarias por producto | `id, producto_id, venta_id, fecha, cantidad_merma, motivo, created_at` |
| `fact_predicciones` | Predicciones ML futuras | `id, producto_id, fecha_proyectada, demanda_estimada, confianza_prediccion, created_at` |
| `fact_ordenes_compra` | Órdenes de reposición | `id, proveedor_id, insumo_id, fecha_orden, cantidad, precio_unitario, estado, created_at` |

### Relaciones entre tablas

```
DimProducto (1) ──────< (N) FactVenta
DimProducto (1) ──────< (N) FactMerma
DimProducto (1) ──────< (N) FactPrediccion
DimProducto (1) ──────< (N) FichaTecnica

FactVenta (1) ──────< (N) FactMerma (cascade delete)

Proveedor (1) ──────< (N) InsumoCritico
Proveedor (1) ──────< (N) OrdenCompra

InsumoCritico (1) ──────< (N) FichaTecnica
InsumoCritico (1) ──────< (N) OrdenCompra
```

### Estado actual de datos

- **Período histórico:** 2024-05-01 → 2025-04-29 (364 días)
- **Registros ventas:** 2,548 (7 productos × ~364 días)
- **Registros mermas:** 2,231
- **Registros clima:** 364 días (+ 15 días futuros)
- **Proveedores:** 3
- **Insumos críticos:** 7
- **Fichas técnicas:** 22 relaciones insumo-producto
- **Predicciones activas:** 49 (7 productos × 7 días futuros)

---

## 5. Módulo ML — Detalles técnicos

### Algoritmo: Random Forest Regressor (scikit-learn)

**Estrategia:** Un modelo `.pkl` por producto (mejor captura patrones individuales).

### Features usados (13 variables)

| Categoría | Feature | Descripción |
|---|---|---|
| **Temporales** | `dia_semana` | Día de la semana (0=Lunes, 6=Domingo) |
| | `mes` | Mes del año (1-12) |
| | `dia_mes` | Día del mes (1-31) |
| | `dia_anio` | Día del año (1-366) |
| | `es_finde` | Boolean: 1 si es sábado o domingo |
| **Contextuales** | `es_feriado` | Boolean: 1 si es feriado peruano |
| | `tiene_evento` | Boolean: 1 si tiene evento especial |
| | `temperatura` | Temperatura promedio en °C |
| | `condicion_encoded` | Condición climática (0-4) |
| **Históricos** | `ventas_lag_1` | Ventas del día anterior |
| | `ventas_lag_7` | Ventas de hace 7 días |
| | `ventas_rolling_7` | Promedio móvil últimos 7 días |
| | `ventas_rolling_30` | Promedio móvil últimos 30 días |

### Hiperparámetros del modelo

```python
RandomForestRegressor(
    n_estimators=200,      # Número de árboles
    max_depth=8,          # Profundidad máxima
    min_samples_split=5,  # Mínimo samples para dividir
    min_samples_leaf=3,   # Mínimo samples por hoja
    max_features="sqrt",  # Features por split
    random_state=42,      # Semilla reproducible
    n_jobs=-1,            # Usar todos los cores
)
```

**Split de evaluación:** últimos 30 días = test (split temporal, no aleatorio).

### Métricas obtenidas (entrenamiento inicial)

| Producto | MAE (uds) | R² | RMSE | Observaciones |
|---|---|---|---|---|
| Pan Frances | 36.32 | 0.535 | - | Volumen alto, varianza natural |
| Pan Integral | 13.72 | 0.627 | - | Buen rendimiento |
| Pan de Molde | 2.43 | 0.469 | - | Volumen bajo |
| Croissant | 4.28 | 0.665 | - | Mejor R² del conjunto |
| Empanada de Carne | 7.64 | 0.497 | - | Aceptable |
| Torta de Cumpleaños | 0.49 | 0.026 | - | Bajo esperado (demanda esporádica) |
| Galletas de Avena | 10.26 | 0.519 | - | Aceptable |

### Integración con clima real

- **Proveedor:** Open-Meteo API (gratuita, sin API key)
- **Coordenadas:** Pacasmayo, Perú (Lat=-7.4006, Lon=-79.5714)
- **Datos obtenidos:** temperature_2m_max, temperature_2m_min, weathercode
- **Fallback:** Si falla la API, usa promedios históricos

### Flujo de uso del ML

```
1. POST /datos/semilla      → Carga 365 días de datos históricos (solo 1 vez)
2. POST /ml/entrenar        → Entrena Random Forest y guarda .pkl
3. POST /predicciones/generar?n_dias=7  → Genera predicciones y guarda en BD
4. GET  /predicciones/      → Consulta predicciones guardadas
5. GET  /predicciones/vs-real → Evalúa precisión vs ventas reales (OE6)
6. POST /clima/sincronizar   → Sincroniza clima real de Open-Meteo
```

---

## 6. API — Endpoints completos

Base URL: `http://localhost:8000`

### Productos
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/productos/` | Listar todos |
| POST | `/productos/` | Crear producto |
| GET | `/productos/{id}` | Obtener uno |
| PUT | `/productos/{id}` | Actualizar |
| DELETE | `/productos/{id}` | Eliminar |

### Ventas y Mermas
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/ventas/` | Listar ventas con nombre de producto |
| POST | `/ventas/` | Registrar venta (con automatismos) |
| DELETE | `/ventas/{id}` | Eliminar venta y recuperar stock |
| GET | `/mermas/` | Listar mermas |
| POST | `/mermas/` | Registrar merma manual |
| DELETE | `/mermas/{id}` | Eliminar merma |
| GET | `/mermas/analisis` | Agrupación por motivo y producto (OE1) |

**Automatismos en POST /ventas/:**
- Si `cantidad_producida > cantidad_vendida`: genera merma automática con motivo
- Si `cantidad_producida > 0`: descuenta insumos según ficha técnica

### Insumos y Stock
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/insumos/` | Listar insumos |
| POST | `/insumos/` | Crear insumo |
| PUT | `/insumos/{id}` | Actualizar stock/datos |
| GET | `/insumos/alertas/` | Insumos bajo stock mínimo |

### Predicciones ML
| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/datos/semilla` | Carga datos históricos sintéticos |
| POST | `/ml/entrenar` | Entrena Random Forest para todos los productos |
| GET | `/ml/metricas` | Obtiene métricas de modelos entrenados |
| POST | `/predicciones/generar?n_dias=7` | Genera y guarda predicciones |
| GET | `/predicciones/` | Listar predicciones guardadas |
| GET | `/predicciones/vs-real?dias=30` | Evalúa predicción vs realidad (OE6) |

### Clima
| Método | Endpoint | Descripción |
|---|---|---|
| GET/POST | `/clima/` | Datos climáticos |
| GET | `/clima/{fecha}` | Clima de un día específico |
| POST | `/clima/sincronizar?dias=7` | Sincroniza con Open-Meteo API |

### Proveedores, Fichas Técnicas, Órdenes
| Método | Endpoint | Descripción |
|---|---|---|
| GET/POST | `/proveedores/` | Catálogo de proveedores |
| GET/POST | `/fichas-tecnicas/` | Recetas (insumo por producto) |
| GET/POST | `/ordenes-compra/` | Órdenes de compra |
| PUT | `/ordenes-compra/{id}/estado?estado=...` | Cambiar estado (pendiente/recibido/cancelado) |

### Dashboard y Reportes
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/dashboard/resumen` | KPIs: ventas, mermas, alertas, predicción semana |
| GET | `/sistema/estado` | Health check completo del sistema |

---

## 7. Frontend Streamlit — Estructura de páginas

### Navegación principal

```
Operacion Diaria 🏪
├── Resumen (default)
├── Registro Diario
├── Predicciones
├── Mermas
├── Inventario
├── Ordenes de Compra
└── Reportes Financieros

Sistema (Tecnico) ⚙️
└── Estadisticas del Modelo
```

### Página 1: Resumen (pages/Resumen.py)
- **Objetivo:** Dashboard KPIs principal
- **Componentes:**
  - Métricas: Ventas hoy, Mermas hoy, % Merma 30d, Insumos en alerta
  - Gráfico: Producción sugerida (próximos 7 días)
  - Botones de navegación rápida

### Página 2: Registro Diario (pages/Registro_Diario.py)
- **Objetivo:** Registro de ventas y mermas con automatismos
- **Tabs:**
  - Registrar Venta: producto, fecha, cantidad vendida, cantidad producida
  - Registrar Merma Manual: para mermas no causadas por sobreproducción
  - Historial: últimas 20 ventas/mermas con opción de eliminación

### Página 3: Predicciones (pages/Predicciones.py)
- **Objetivo:** Visualizar predicciones del modelo ML
- **Componentes:**
  - Botón: Generar nuevas predicciones
  - Botón: Sincronizar clima (Open-Meteo)
  - Gráfico de barras: demanda por producto y fecha
  - Tabla detallada de predicciones
  - Gráfico circular: distribución de producción semanal

### Página 4: Análisis de Mermas (pages/Analisis_Mermas.py)
- **Objetivo:** Diagnóstico de causas raíz (OE1)
- **Componentes:**
  - KPIs: % Merma Global, Total Unidades, Causas identificadas
  - Gráfico Pareto por motivo
  - Gráfico de barras por producto
  - Tablas detalladas
  - Últimas 20 mermas registradas

### Página 5: Inventario (pages/Inventario.py)
- **Objetivo:** Gestión de stock de insumos críticos
- **Componentes:**
  - Tabla de productos con precios y márgenes
  - Métricas: Total Insumos, Stock OK, Bajo Stock
  - Estado visual de stock por insumo (gráfico de barras)
  - Actualización manual de stock

### Página 6: Órdenes de Compra (pages/Ordenes_Compra.py)
- **Objetivo:** Gestión de órdenes de reposición
- **Tabs:**
  - Ver órdenes: lista con filtros por estado, actualización de estado
  - Crear orden: formulario para nueva orden

### Página 7: Reportes Financieros (pages/Reportes_Financieros.py)
- **Objetivo:** Análisis financiero con exportación PDF
- **Componentes:**
  - Filtro de fechas
  - KPIs: Ingresos Totales, Costo Producción, Pérdida por Merma, Utilidad Bruta
  - Gráficos: Ingresos por producto, Evolución de ingresos
  - Tabla detalle por producto
  - Exportar a PDF (genera PDF con gráficos)

### Página 8: Modelo Estadístico (pages/Modelo_Estadistico.py)
- **Objetivo:** Métricas de evaluación del modelo ML
- **Componentes:**
  - Botón: Reentrenar modelos
  - KPIs: Modelos entrenados, R² promedio, MAE promedio, Algoritmo
  - Gráfico R² por producto
  - Gráficos MAE y RMSE
  - Tabla de métricas completas
  - Comparación Predicción vs Ventas Reales (gráfico interactivo)

---

## 8. Objetivos de tesis y estado de avance

| OE | Objetivo | Estado |
|---|---|---|
| OE1 | Diagnosticar mermas y causas raíz | ✅ Implementado (`/mermas/analisis`) |
| OE2 | Modelo ML de predicción (Random Forest) | ✅ Implementado (`trainer.py`, `predictor.py`, `features.py`) |
| OE3 | API RESTful que exponga predicciones | ✅ Implementado (`main.py` completo con 40+ endpoints) |
| OE4 | Automatización n8n — órdenes automáticas | ✅ Workflow configurado (ver `n8n-workflow.json` y `setup_n8n_workflow.py`) |
| OE5 | Dashboard interactivo con KPIs en tiempo real | ✅ Implementado (Streamlit + Nuevo Django SPA) |
| OE6 | Evaluar impacto (≥ 20% reducción mermas) | 🟡 Endpoint `/predicciones/vs-real` listo, evaluación futura |

---

## 9. Convenciones y reglas del proyecto

### Python / FastAPI
- Usar `Optional[tipo]` en vez de `tipo | None` para compatibilidad con Python 3.9+
- Todos los schemas Pydantic usan `class Config: from_attributes = True`
- La sesión de BD se inyecta siempre con `Depends(get_db)`
- Validar existencia de FK antes de insertar (producto, insumo, proveedor)

### Encoding en Windows
- **NO usar emojis** en `print()` dentro de scripts `.py` ejecutados en PowerShell
- PowerShell usa codificación `cp1252` que no soporta caracteres Unicode extendidos
- Usar texto plano: `[OK]`, `[ERROR]`, `->` en vez de ✅, ❌, →

### Importaciones en el módulo ML
- Los scripts en `backend/ml/` usan `sys.path.insert(0, "..")` para importar `models` y `database`
- Al importar desde `main.py` vía API, los imports son relativos al directorio `backend/`

### Docker
- En PowerShell, el separador de comandos es `;` (no `&&`)
  - Correcto: `docker-compose down -v; docker-compose up -d`
  - Incorrecto: `docker-compose down -v && docker-compose up -d`
- `docker-compose down -v` elimina los volúmenes (borra la BD) — úsalo solo para reset completo

### Modelos ML
- Los archivos `.pkl` se guardan en `backend/ml/models_trained/{producto_id}.pkl`
- Las métricas se guardan en `backend/ml/models_trained/{producto_id}_meta.json`
- El `producto_id` corresponde al `id` auto-incremental de `dim_productos`
- Reentrenar sobrescribe los `.pkl` existentes

---

## 10. Datos sintéticos — Patrones modelados

Los datos históricos en `seed_data.py` simulan:

| Patrón | Detalle |
|---|---|
| **Estacionalidad semanal** | Sábado +35%, Domingo +30%, Lunes −30% |
| **Feriados peruanos** | +50% en días feriados nacionales |
| **Eventos locales** | +40% en Día de la Madre, San Valentín, Fiestas Patrias |
| **Verano costero** | +15% en Dic-Mar (costa norte, Pacasmayo) |
| **Temperatura Pacasmayo** | 18°C (invierno) a 27°C (verano), σ=1.5°C |
| **Clima** | 65% soleado, 20% parcialmente nublado, raramente lluvia |
| **Buffer de producción** | 10–25% sobre la demanda → genera mermas realistas |

### Productos y volúmenes base

| Producto | Categoría | Precio | Costo | Base/día |
|---|---|---|---|---|
| Pan Frances | Pan de mesa | S/ 0.20 | S/ 0.10 | 200 uds |
| Pan Integral | Pan de mesa | S/ 0.30 | S/ 0.15 | 80 uds |
| Pan de Molde | Pan especial | S/ 5.00 | S/ 2.50 | 15 uds |
| Croissant | Bollería | S/ 2.50 | S/ 1.20 | 30 uds |
| Empanada de Carne | Salados | S/ 1.50 | S/ 0.70 | 50 uds |
| Torta de Cumpleaños | Pasteles | S/ 50.00 | S/ 25.00 | 2 uds |
| Galletas de Avena | Dulces | S/ 0.50 | S/ 0.20 | 60 uds |

### Insumos críticos inicializados

| Insumo | Stock Actual | Stock Mínimo | Unidad | Proveedor |
|---|---|---|---|---|
| Harina de Trigo | 200 Kg | 50 Kg | Kg | Molinos del Norte SAC |
| Azúcar | 80 Kg | 20 Kg | Kg | Distribuidora Lácteos La Victoria |
| Mantequilla | 30 Kg | 10 Kg | Kg | Distribuidora Lácteos La Victoria |
| Levadura | 5 Kg | 2 Kg | Kg | Molinos del Norte SAC |
| Huevos | 300 uds | 60 uds | Unidades | Agropecuaria Los Andes |
| Leche | 50 Lt | 15 Lt | Litros | Distribuidora Lácteos La Victoria |
| Sal | 25 Kg | 5 Kg | Kg | Molinos del Norte SAC |

### Fichas técnicas (recetas)

Cada producto tiene una receta con consumo de insumos por unidad:
- Pan Frances: 100g harina + 2g levadura + 5g sal
- Pan Integral: 90g harina + 2g levadura + 5g sal
- Croissant: 80g harina + 30g mantequilla + 1 huevo
- (etc.)

---

## 11. Variables de entorno (.env)

```env
DATABASE_URL=postgresql://eduardo:123456@localhost:5432/panaderia_victoria
```

`database.py` carga este archivo automáticamente con `python-dotenv`. El fallback hardcodeado usa los mismos valores.

---

## 12. Scripts de utilidad

### reset_db.py
Script para resetear completamente la base de datos (elimina todas las tablas y las recrea).

### _add_delete_mermas.py
Script auxiliar para agregar o eliminar mermas masivas (uso interno).

### _patch_motivos.py
Script para actualizar motivos de mermas en la base de datos.

---

## 13. Documentación adicional

El proyecto incluye documentación en `docs/`:
- `docs/index.md` - Índice de documentación
- `docs/frontend/index.md` - Documentación del frontend
- `docs/frontend/pages.md` - Detalle de cada página
- `docs/frontend/README.md` - Guía del frontend
- `docs/backend/API.md` - Documentación de la API
- `docs/backend/ML.md` - Documentación del módulo ML
- `docs/backend/README.md` - Guía del backend

---

## 14. Próximos pasos (pendientes)

### Prioritario
1. **Módulo de evaluación OE6** — Tras acumular datos reales:
   - Comparar predicción vs real con `/predicciones/vs-real`
   - Calcular % reducción de mermas mensual
   - Exportar reporte en PDF/Excel para la tesis

### n8n — Workflow implementado
El workflow de automatización de órdenes de compra ya está configurado:

**Archivos:**
- `n8n-workflow.json` — Definición del workflow para importar en n8n
- `setup_n8n_workflow.py` — Script Python para importar automáticamente

**Flujo del workflow:**
```
Trigger (8:00 AM diario)
  → GET /insumos/alertas/ (detecta insumos bajo stock)
  → Filtra insumos críticos (necesita_reorden = true)
  → GET /proveedores/ (obtiene datos del proveedor)
  → POST /ordenes-compra/ (crea orden automática)
  → Email al proveedor (si tiene email configurado)
  → Resumen de órdenes creadas
```

**Para activar:**
```powershell
# 1. Asegurar que Docker está corriendo
docker-compose up -d

# 2. Asegurar que el backend está corriendo
cd backend
uvicorn main:app --reload

# 3. Importar workflow (en terminal separada desde raíz)
python setup_n8n_workflow.py
```

### Mejoras opcionales
- Agregar `Alembic` para migraciones de BD en vez de `drop_all/create_all`
- Configurar autenticación JWT en la API para producción
- Agregar endpoint `POST /ventas/bulk` para importar desde Excel
- Mejorar integración con n8n para notificaciones automáticas

---

## 15. URLs de referencia rápida

| Recurso | URL |
|---|---|
| API Principal | `http://localhost:8000` |
| Documentación API (Swagger) | `http://localhost:8000/docs` |
| Dashboard Streamlit | `http://localhost:8501` |
| pgAdmin | `http://localhost:8080` |
| n8n (Workflows) | `http://localhost:5678` |
| Open-Meteo (Clima) | `https://api.open-meteo.com/v1/forecast` |

---

*Última actualización: Abril 2026 — Sistema completo implementado para Tesis UNT 2026-I*