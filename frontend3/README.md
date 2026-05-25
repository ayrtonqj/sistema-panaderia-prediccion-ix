# Panadería Victoria - Frontend 3 (React)

Sistema de gestión predictiva para panadería con 7 modelos de Machine Learning.

## 🧠 Sistema Predictivo Multimodelo

El sistema implementa **7 algoritmos de predicción** que se comparan automáticamente para elegir el mejor modelo por cada producto.

### Los 7 Modelos

| # | Algoritmo | Librería | Tipo | Ideal para |
|---|-----------|----------|------|------------|
| 1 | **Random Forest** | scikit-learn | Árboles ensemble | Datos tabulares con interacciones no lineales |
| 2 | **Linear Regression** | scikit-learn | Regresión lineal | Línea base de comparación |
| 3 | **Gradient Boosting** | scikit-learn | Árboles gradient-boosted | Mayor precisión que RF en datos pequeños |
| 4 | **SARIMA** | statsmodels | Serie temporal estacional | Patrones semanales y tendencias |
| 5 | **Prophet** | Meta/Facebook | Descomposición aditiva | Feriados peruanos y estacionalidad |
| 6 | **MLP Neural Network** | scikit-learn | Red neuronal (2 capas) | Patrones complejos no lineales |
| 7 | **Ensemble (RF+GB+LR)** | scikit-learn | Voting Regressor | Promedio ponderado de los 3 mejores |

### Pipeline ML

```
📥 Datos históricos (ventas + clima)
        ↓
   ┌─────────────────┐
   │  build_features │  ← 13 features: temporales, clima, lags, rolling windows
   └────────┬────────┘
            ↓
   ┌─────────────────┐
   │  entrenar_todos │  ← Entrena 7 modelos por cada producto (24 productos)
   └────────┬────────┘
            ↓
   ┌─────────────────┐
   │  comparador     │  ← Evalúa con últimos 30 días, elige el de menor RMSE
   └────────┬────────┘
            ↓
   ┌─────────────────────────┐
   │  best_model.json        │  ← {producto_id: "nombre_algoritmo"}
   │  best_{id}.pkl          │  ← Modelo serializado (joblib)
   │  best_{id}_meta.json    │  ← Métricas de todos los modelos
   └────────┬────────┘
            ↓
   ┌─────────────────┐
   │  generar_predicciones │  ← Usa el mejor modelo por producto
   └────────┬────────┘
            ↓
   📊 fact_predicciones (con algoritmo_utilizado + confianza R²)
```

### Features (13 variables)

| Categoría | Variables |
|-----------|-----------|
| **Temporales** | día_semana, mes, día_mes, día_año, es_finde |
| **Contextuales** | es_feriado, tiene_evento, temperatura, condición_clima |
| **Lags** | ventas_lag_1 (ayer), ventas_lag_7 (misma semana anterior) |
| **Rolling** | ventas_rolling_7, ventas_rolling_30 (promedios móviles) |

### Endpoints del Backend

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/ml/entrenar` | POST | Entrena todos los modelos y compara resultados |
| `/ml/comparar` | POST | Ejecuta solo la comparación (entrena + evalúa + rankea) |
| `/ml/metricas` | GET | Métricas del mejor modelo por producto (R², MAE, RMSE) |
| `/ml/mejores-modelos` | GET | Mapeo producto → mejor algoritmo |
| `/predicciones/generar` | POST | Genera predicciones usando el mejor modelo |
| `/predicciones/vs-real` | GET | Compara predicciones vs ventas reales (MAE global) |

### Estructura de Archivos ML

```
backend/ml/
├── features.py              # Ingeniería de features (13 variables)
├── weather_api.py           # API Open-Meteo para clima real
├── seed_data.py             # Generador de datos sintéticos
├── trainer.py               # Entrenamiento de 7 modelos por producto
├── predictor.py             # Predicción usando el mejor modelo
├── comparador.py            # Comparación y ranking de modelos
├── models/
│   ├── __init__.py
│   └── registry.py          # Catálogo de los 7 algoritmos
└── models_trained/
    ├── best_model.json      # Mapeo producto → mejor algoritmo
    ├── best_{id}.pkl        # Mejor modelo serializado
    ├── best_{id}_meta.json  # Métricas de todos los modelos
    ├── {id}.pkl             # Modelo legacy (Random Forest)
    └── {id}_meta.json       # Métricas legacy
```

### Dependencias Python

```txt
scikit-learn>=1.3.0
statsmodels>=0.14.0
prophet>=1.1.0  # Opcional: si no está, se salta ese modelo
pandas>=2.0.0
numpy>=1.24.0
joblib>=1.3.0
httpx>=0.25.0
```

### Instalación de Dependencias ML

```bash
pip install scikit-learn statsmodels prophet pandas numpy joblib httpx
```

## Ejecución

```bash
# Backend (FastAPI)
cd backend
uvicorn main:app --reload --port 8000

# Frontend (React + Vite)
cd frontend3
npm run dev
```

## Flujo de Trabajo Recomendado

1. **Seed de datos**: `POST /datos/semilla` (genera 365 días de datos sintéticos)
2. **Entrenar modelos**: `POST /ml/comparar` (entrena 7 modelos por producto)
3. **Ver resultados**: Revisar la tabla de comparación en Predicciones
4. **Generar predicciones**: Click en "Generar Predicciones (7 días)"
5. **Monitorear**: Ver R², MAE, RMSE por producto en la página de Predicciones
