# 📚 Documentación del Sistema Predictivo - Panadería Victoria

> Guía completa para entender, configurar y usar el sistema.

---

## 📂 Índice de Documentos

### Backend
| Documento | Descripción |
|-----------|-------------|
| **[backend/README.md](backend/README.md)** | Explicación del backend: estructura, modelos de datos, flujo general |
| **[backend/ML.md](backend/ML.md)** | Explicación detallada del módulo de Machine Learning |
| **[backend/API.md](backend/API.md)** | Referencia de todos los endpoints de la API REST |

### Frontend
| Documento | Descripción |
|-----------|-------------|
| **[frontend/README.md](frontend/README.md)** | Visión general del frontend Analítico (Streamlit) |
| **[frontend/pages.md](frontend/pages.md)** | Guía detallada de cada página del sistema Streamlit |
| **frontend2** | Dashboard operativo ultrarrápido creado con Django y HTMX |

---

## 🎯 ¿Qué hace este sistema?

El Sistema Predictivo de Producción ayuda a la **Panadería Victoria** a:

1. **Predecir demanda** - Cuántos panes se venderán mañana/semana próxima
2. **Reducir mermas** - Evitar sobreproducción y subproducción
3. **Gestionar inventario** - Alertar cuando faltan insumos
4. **Generar órdenes** - Automatizar compras de reposición
5. **Analizar finanzas** - Ver ingresos, costos y pérdidas

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                 │
│  ┌─────────────────────────┐   ┌─────────────────────────────┐  │
│  │  Frontend Operativo     │   │   Frontend Analítico        │  │
│  │   (Django + HTMX)       │   │      (Streamlit)            │  │
│  │    localhost:8001       │   │    localhost:8501           │  │
│  └───────────┬─────────────┘   └─────────────┬───────────────┘  │
└──────────────┼───────────────────────────────┼──────────────────┘
               │                               │
               └────────────────┬──────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │      API REST (FastAPI)      │
              │       localhost:8000         │
              └─────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   PostgreSQL  │   │   ML Module   │   │   n8n         │
│   (Datos)      │   │  (Predictor) │   │ (Automatiz.) │
└───────────────┘   └───────────────┘   └───────────────┘
```

---

## 🚀 Inicio Rápido

### 1. Levantar el backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 2. Levantar los frontends
**Frontend Analítico (Streamlit):**
```bash
cd frontend
streamlit run app.py
```

**Frontend Operativo (Django):**
```bash
cd frontend2
python manage.py runserver 8001
```

### 3. Abrir en navegador
- Dashboard Django (Operativo): `http://localhost:8001`
- Dashboard Streamlit (Analítico): `http://localhost:8501`
- API Docs: `http://localhost:8000/docs`

---

## 📋 Primeros Pasos (para usuarios)

1. **Cargar datos históricos** (si es la primera vez)
   - Ve a: `Registro Diario` → pestaña "Importar datos de prueba"

2. **Entrenar modelos ML**
   - Ve a: `Modelo ML` → botón "Entrenar Modelos"

3. **Generar predicciones**
   - Ve a: `Predicciones` → botón "Generar nuevas predicciones"

4. **Revisar el Dashboard**
   - Verás las predicciones de hoy y mañana

---

## 📚 Para Desarrolladores

### Estructura del proyecto

```
panaderia/
├── backend/           # API FastAPI
│   ├── main.py        # Endpoints de la API
│   ├── database.py    # Conexión a PostgreSQL
│   ├── models.py      # Modelos de la base de datos
│   └── ml/            # Módulo de Machine Learning
│       ├── trainer.py      # Entrenamiento
│       ├── predictor.py    # Predicciones
│       ├── features.py     # Features del modelo
│       ├── weather_api.py  # Clima
│       └── seed_data.py    # Datos de ejemplo
│
├── frontend/          # Interfaz Analítica (Streamlit)
│   ├── app.py         
│   └── pages/         
│
├── frontend2/         # Interfaz Operativa (Django)
│   ├── manage.py
│   ├── core/          # Views y lógica (consume API)
│   └── templates/     # HTML con HTMX
│
├── docs/              # Esta documentación
│   ├── README.md
│   ├── ML.md
│   └── API.md
│
└── .env               # Variables de entorno
```

---

## 🛠️ Tecnologías Usadas

| Componente | Tecnología |
|------------|------------|
| Backend API | FastAPI (Python) |
| Base de datos | PostgreSQL |
| ORM | SQLAlchemy |
| Machine Learning | scikit-learn (Random Forest) |
| Dashboard | Streamlit |
| Visualización | Plotly |
| API de clima | Open-Meteo (gratuito) |
| Automatización | n8n (opcional) |

---

## 📞 Soporte

Si tienes dudas sobre el sistema:

1. **Consulta la documentación** en la carpeta `docs/`
2. **Revisa los endpoints** en `http://localhost:8000/docs`
3. **Mira los logs** en la terminal donde corre uvicorn

---

*Sistema Predictivo de Producción - Tesis Panadería Victoria*