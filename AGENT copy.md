# AGENT.md — Sistema Predictivo Panadería Victoria

Guía de contexto completo para agentes de IA que trabajen en este proyecto.
Leer este archivo **primero** antes de cualquier tarea de desarrollo.

---

## 1. Descripción del proyecto

**Nombre:** Sistema Predictivo de Producción y Automatización de Cadena de Suministro — Panadería Victoria

**Institución:** Universidad Nacional de Trujillo (UNT) — Tesis de Ingeniería 2026-I

**Objetivo académico:** Reducir las mermas de producción en la Panadería Victoria de Pacasmayo en **≥ 20%** mediante un sistema basado en Machine Learning y Business Intelligence.

**Stack tecnológico:**
- **Backend API:** FastAPI + SQLAlchemy + PostgreSQL
- **ML:** scikit-learn (Random Forest Regressor), un modelo por producto
- **Frontend:** Streamlit (dashboard interactivo)
- **Automatización:** n8n (flujos de órdenes de compra automáticas)
- **Infraestructura:** Docker Compose (PostgreSQL + pgAdmin + n8n)
- **ORM:** SQLAlchemy 2.x con `from_attributes = True`
- **Python:** 3.14 (Windows, PowerShell)

---

## 2. Estructura del proyecto

```
d:\.UNT\2026-I\TESIS I\panaderia\
│
├── AGENT.md                        ← Este archivo
├── tesis.md                        ← Objetivos y problema de investigación
├── .env                            ← Credenciales BD (NO commitear)
├── docker-compose.yml              ← PostgreSQL + pgAdmin + n8n
├── requirements.txt                ← Dependencias Python
│
├── backend/
│   ├── main.py                     ← API FastAPI completa (punto de entrada)
│   ├── models.py                   ← Modelos SQLAlchemy (schema BD)
│   ├── database.py                 ← Conexión BD (lee .env)
│   └── ml/
│       ├── __init__.py
│       ├── features.py             ← Ingeniería de características
│       ├── seed_data.py            ← Generador de datos históricos sintéticos
│       ├── trainer.py              ← Entrenamiento Random Forest
│       ├── predictor.py            ← Generación de predicciones
│       └── models_trained/
│           ├── 1.pkl               ← Pan Frances
│           ├── 2.pkl               ← Pan Integral
│           ├── 3.pkl               ← Pan de Molde
│           ├── 4.pkl               ← Croissant
│           ├── 5.pkl               ← Empanada de Carne
│           ├── 6.pkl               ← Torta de Cumpleaños
│           └── 7.pkl               ← Galletas de Avena
│
├── frontend/
│   └── app.py                      ← Dashboard Streamlit (EN DESARROLLO)
│
└── venv/                           ← Entorno virtual Python
```

---

## 3. Servicios en ejecución

| Servicio | URL | Credenciales |
|---|---|---|
| **FastAPI** (backend) | `http://localhost:8000` | — |
| **FastAPI Docs** | `http://localhost:8000/docs` | — |
| **Streamlit** (frontend) | `http://localhost:8501` | — |
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

# Frontend (abrir terminal en frontend/)
cd frontend
streamlit run app.py
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
| `fact_mermas` | Mermas diarias por producto | `id, producto_id, fecha, cantidad_merma, motivo, created_at` |
| `fact_predicciones` | Predicciones ML futuras | `id, producto_id, fecha_proyectada, demanda_estimada, confianza_prediccion, created_at` |
| `fact_ordenes_compra` | Órdenes de reposición | `id, proveedor_id, insumo_id, fecha_orden, cantidad, precio_unitario, estado, created_at` |

### Estado actual de datos

- **Período histórico:** 2024-05-01 → 2025-04-29 (364 días)
- **Registros ventas:** 2,548 (7 productos × ~364 días)
- **Registros mermas:** 2,231
- **Registros clima:** 364 días
- **Proveedores:** 3
- **Insumos críticos:** 7
- **Predicciones activas:** 49 (7 productos × 7 días futuros)

---

## 5. Módulo ML — Detalles técnicos

### Algoritmo: Random Forest Regressor (scikit-learn)

**Estrategia:** Un modelo `.pkl` por producto (mejor captura patrones individuales).

**Features usados (13 variables):**
```
dia_semana, mes, dia_mes, dia_anio,
es_finde, es_feriado, tiene_evento,
temperatura, condicion_encoded,
ventas_lag_1, ventas_lag_7,
ventas_rolling_7, ventas_rolling_30
```

**Hiperparámetros del modelo:**
```python
RandomForestRegressor(
    n_estimators=200,
    max_depth=8,
    min_samples_split=5,
    min_samples_leaf=3,
    max_features="sqrt",
    random_state=42,
)
```

**Split de evaluación:** últimos 30 días = test (split temporal, no aleatorio).

### Métricas obtenidas (entrenamiento inicial)

| Producto | MAE | R² | Observaciones |
|---|---|---|---|
| Pan Frances | 36.32 | 0.535 | Volumen alto, varianza natural |
| Pan Integral | 13.72 | 0.627 | Buen rendimiento |
| Pan de Molde | 2.43 | 0.469 | Volumen bajo |
| Croissant | 4.28 | 0.665 | Mejor R² del conjunto |
| Empanada de Carne | 7.64 | 0.497 | Aceptable |
| Torta de Cumpleaños | 0.49 | 0.026 | Bajo esperado (demanda esporádica) |
| Galletas de Avena | 10.26 | 0.519 | Aceptable |

### Flujo de uso del ML

```
1. POST /datos/semilla      → Carga 365 días de datos históricos (solo 1 vez)
2. POST /ml/entrenar        → Entrena Random Forest y guarda .pkl
3. POST /predicciones/generar?n_dias=7  → Genera predicciones y guarda en BD
4. GET  /predicciones/      → Consulta predicciones guardadas
5. GET  /predicciones/vs-real → Evalúa precisión vs ventas reales (OE6)
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
| POST | `/ventas/` | Registrar venta |
| GET | `/mermas/` | Listar mermas |
| POST | `/mermas/` | Registrar merma |
| GET | `/mermas/analisis` | Agrupación por motivo y producto (OE1) |

### Insumos y Stock
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/insumos/` | Listar insumos |
| POST | `/insumos/` | Crear insumo |
| PUT | `/insumos/{id}` | Actualizar stock/datos |
| GET | `/insumos/alertas/` | Insumos bajo stock mínimo |

### ML y Predicciones
| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/datos/semilla` | Carga datos históricos sintéticos |
| POST | `/ml/entrenar` | Entrena Random Forest para todos los productos |
| POST | `/predicciones/generar?n_dias=7` | Genera y guarda predicciones |
| GET | `/predicciones/` | Listar predicciones guardadas |
| GET | `/predicciones/vs-real?dias=30` | Evalúa predicción vs realidad (OE6) |

### Dashboard y Reportes
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/dashboard/resumen` | KPIs: ventas, mermas, alertas, predicción semana |

### Clima, Proveedores, Fichas, Órdenes
| Método | Endpoint | Descripción |
|---|---|---|
| GET/POST | `/clima/` | Datos climáticos |
| GET | `/clima/{fecha}` | Clima de un día específico |
| GET/POST | `/fichas-tecnicas/` | Recetas (insumo por producto) |
| GET/POST | `/proveedores/` | Catálogo de proveedores |
| GET/POST | `/ordenes-compra/` | Órdenes de compra |
| PUT | `/ordenes-compra/{id}/estado` | Cambiar estado (pendiente/recibido/cancelado) |

---

## 7. Objetivos de tesis y estado de avance

| OE | Objetivo | Estado |
|---|---|---|
| OE1 | Diagnosticar mermas y causas raíz | ✅ Implementado (`/mermas/analisis`) |
| OE2 | Modelo ML de predicción (Random Forest) | ✅ Implementado (`trainer.py`, `predictor.py`) |
| OE3 | API RESTful que exponga predicciones | ✅ Implementado (`main.py` completo) |
| OE4 | Automatización n8n — órdenes automáticas | 🟡 n8n en Docker, workflow pendiente de configurar |
| OE5 | Dashboard Streamlit con KPIs en tiempo real | 🔴 Pendiente (solo formulario básico actual) |
| OE6 | Evaluar impacto (≥ 20% reducción mermas) | 🟡 Endpoint `/predicciones/vs-real` listo, evaluación futura |

---

## 8. Convenciones y reglas del proyecto

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
- El `producto_id` corresponde al `id` auto-incremental de `dim_productos`
- Reentrenar sobrescribe los `.pkl` existentes

---

## 9. Datos sintéticos — Patrones modelados

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

---

## 10. Variables de entorno (.env)

```env
DATABASE_URL=postgresql://eduardo:123456@localhost:5432/panaderia_victoria
```

`database.py` carga este archivo automáticamente con `python-dotenv`. El fallback hardcodeado usa los mismos valores.

---

## 11. Próximos pasos (pendientes)

### Prioritario
1. **Frontend Streamlit** — Reconstruir `frontend/app.py` con:
   - Página 1: Dashboard KPIs (ventas, mermas, % merma, alertas)
   - Página 2: Predicciones (gráfico de barras por producto, próximos 7 días)
   - Página 3: Estado de inventario (tabla con semáforo rojo/amarillo/verde)
   - Página 4: Órdenes de compra (crear, ver estado, actualizar)
   - Página 5: Análisis de mermas (Pareto por motivo y producto)

2. **Workflow n8n** — Configurar en `localhost:5678`:
   - Trigger: cada 24h o al detectar alerta en `/insumos/alertas/`
   - Acción: crear orden de compra automática via `POST /ordenes-compra/`
   - Notificación: email o mensaje al proveedor

3. **Módulo de evaluación OE6** — Tras acumular datos reales:
   - Comparar predicción vs real con `/predicciones/vs-real`
   - Calcular % reducción de mermas mensual
   - Exportar reporte en PDF/Excel para la tesis

### Mejoras opcionales
- Agregar `Alembic` para migraciones de BD en vez de `drop_all/create_all`
- Guardar métricas R² por producto en `models_trained/{id}_meta.json`
- Configurar autenticación JWT en la API para producción
- Agregar endpoint `POST /ventas/bulk` para importar desde Excel
