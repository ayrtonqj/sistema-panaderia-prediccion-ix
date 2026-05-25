# 🤖 Documentación del Módulo de Machine Learning

> Explicación detallada del sistema de predicción de demanda para principiantes.

---

## 🎯 Objetivo

El sistema predecir **cuántas unidades de cada producto** se venderán en los próximos días, usando Machine Learning (Random Forest).

---

## 🔄 Flujo Completo del ML

```
┌────────────────────────────────────────────────────────────────────────┐
│                         FLUJO DEL MODELO ML                            │
└────────────────────────────────────────────────────────────────────────┘

     ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
     │    DATOS    │ ───▶ │  ENTRENAR   │ ───▶ │  PREDECIR   │
     │  HISTÓRICOS │      │   MODELO    │      │  DEMANDA    │
     └─────────────┘      └─────────────┘      └─────────────┘
          │                     │                     │
          ▼                     ▼                     ▼
    ┌──────────┐          ┌──────────┐          ┌──────────┐
    │ • Ventas │          │Random    │          │Pronóstico│
    │ • Clima  │          │Forest    │          │7 días    │
    │ • Fecha  │          │Regresor  │          │          │
    └──────────┘          └──────────┘          └──────────┘
```

---

## 📂 Archivos del Módulo ML

| Archivo | Función |
|---------|---------|
| `features.py` | Transforma datos en "features" (variables) que el modelo entiende |
| `trainer.py` | Entrena el modelo Random Forest |
| `predictor.py` | Usa el modelo entrenado para predecir ventas futuras |
| `weather_api.py` | Descarga datos del clima desde internet |
| `seed_data.py` | Genera datos de prueba |

---

## 1️⃣ features.py - ¿Cómo preparamos los datos?

### El problema
El modelo no entiende fechas directamente como "lunes" o "diciembre". Necesitamos **convertir fechas en números** que el modelo pueda usar.

### Variables que creamos

```python
# ════════════════════════════════════════════════════════════════════
# VARIABLES TEMPORALES (de la fecha)
# ════════════════════════════════════════════════════════════════════

df["dia_semana"] = df["fecha"].dt.dayofweek  # 0=Lunes, 1=Martes, ..., 6=Domingo
df["mes"] = df["fecha"].dt.month              # 1=Enero, ..., 12=Diciembre
df["dia_mes"] = df["fecha"].dt.day             # 1-31
df["dia_anio"] = df["fecha"].dt.dayofyear      # 1-365
df["es_finde"] = df["dia_semana"].isin([5, 6]).astype(int)  # 1 si es fin de semana
```

**¿Por qué?**
- El modelo aprende que los domingos se vende más
- En diciembre las ventas aumentan
- Los fines de semana hay más movimiento

---

```python
# ════════════════════════════════════════════════════════════════════
# VARIABLES DE CLIMA
# ════════════════════════════════════════════════════════════════════

df["temperatura_promedio"] = clima["temperatura"]  # 18.5, 22.0, etc.
df["condicion_encoded"] = clima["condicion"].map({
    "Soleado": 0,
    "Parcialmente nublado": 1,
    "Nublado": 2,
    "Lluvia ligera": 3,
    "Lluvia": 4
})
```

**¿Por qué?**
- Con lluvia, menos gente sale a comprar pan
- El calor puede reducir el apetito

---

```python
# ════════════════════════════════════════════════════════════════════
# VARIABLES DE CALENDARIO
# ════════════════════════════════════════════════════════════════════

df["es_feriado"] = clima["es_feriado"]  # True/False
df["evento_especial"] = clima["evento_especial"]  # "Día de la Madre", "Navidad"
```

**¿Por qué?**
- Los feriados alteran el patrón normal de ventas
- Eventos especiales aumentan la demanda

---

```python
# ════════════════════════════════════════════════════════════════════
# VARIABLES HISTÓRICAS (Lags - ventas pasadas)
# ════════════════════════════════════════════════════════════════════

# Lag 1: ventas de ayer
df["ventas_lag_1"] = df.sort_values("fecha").groupby("producto")["cantidad_vendida"].shift(1)

# Lag 7: ventas de la semana pasada
df["ventas_lag_7"] = df.sort_values("fecha").groupby("producto")["cantidad_vendida"].shift(7)

# Rolling 7: promedio de los últimos 7 días
df["ventas_rolling_7"] = df.sort_values("fecha").groupby("producto")["cantidad_vendida"].transform(
    lambda x: x.rolling(7, min_periods=1).mean()
)
```

**¿Por qué?**
- Si ayer vendí 50, mañana probablemente venderé ~48-52
- Si la semana pasada vendí 300, esta semana quizás 290-310
- El promedio de 7 días muestra la **tendencia** reciente

---

### Ejemplo completo

**Datos de entrada** (fecha + venta):

| fecha | cantidad_vendida |
|-------|------------------|
| 2024-01-01 | 80 |
| 2024-01-02 | 95 |
| 2024-01-03 | 88 |
| ... | ... |

**Features generados** (lo que "ve" el modelo):

| fecha | dia_semana | mes | es_finde | temperatura | ventas_lag_1 | ventas_lag_7 | ventas_rolling_7 | cantidad_vendida (TARGET) |
|-------|------------|-----|----------|--------------|--------------|--------------|------------------|---------------------------|
| 2024-01-02 | 1 | 1 | 0 | 22.5 | 80 | None | 80.0 | 95 |
| 2024-01-03 | 2 | 1 | 0 | 21.0 | 95 | None | 87.5 | 88 |

---

## 2️⃣ trainer.py - ¿Cómo entrenamos el modelo?

### Concepto: Random Forest

Imagina que preguntas a 100 panaderos experimentados:
> "Si hoy es lunes, está nublado, temperatura 20°C, ayer vendí 50 unidades, ¿cuántos panes venderé hoy?"

Cada panadero dará una respuesta. El **Random Forest** promedia las 100 respuestas para dar una predicción más precisa.

### Código simplificado

```python
from sklearn.ensemble import RandomForestRegressor

def entrenar_modelo(producto_id):
    # 1. Obtener datos de entrenamiento
    df = cargar_datos_de_la_base_de_datos()
    df_producto = df[df["producto_id"] == producto_id]
    
    # 2. Separar features (X) de objetivo (y)
    # X = todo lo que el modelo usa para predecir
    # y = lo que queremos predecir (cantidad_vendida)
    X = df_producto[FEATURE_COLS]  # [dia_semana, mes, temperatura, ...]
    y = df_producto["cantidad_vendida"]
    
    # 3. Dividir datos: 80% entrenamiento, 20% prueba
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    
    # 4. Crear el modelo Random Forest
    modelo = RandomForestRegressor(
        n_estimators=100,    # Cuántos árboles usar
        max_depth=10,       # Qué tan complejos pueden ser los árboles
        random_state=42     # Semilla para reproducibilidad
    )
    
    # 5. ENTRENAR (el modelo aprende de los datos)
    modelo.fit(X_train, y_train)
    
    # 6. Evaluar en datos nuevos (test)
    predicciones = modelo.predict(X_test)
    
    # 7. Calcular métricas
    mae = mean_absolute_error(y_test, predicciones)  # Error promedio
    r2 = r2_score(y_test, predicciones)              # Precisión (0-1)
    
    # 8. Guardar el modelo entrenado
    joblib.dump(modelo, f"models_trained/{producto_id}.pkl")
    
    return {"mae": mae, "r2": r2}
```

---

### Métricas de evaluación

| Métrica | Significado | Ejemplo |
|---------|-------------|---------|
| **MAE** (Error Absoluto Medio) | En promedio, el modelo se equivoca por ±X unidades | MAE = 5.5 → me equivoco por ~5 panes |
| **RMSE** (Root Mean Squared Error) | Similar al MAE, pero penaliza errores grandes | 6.2 |
| **R²** (Coeficiente de determinación) | Porcentaje de variación que explica el modelo | R² = 0.85 → explica el 85% de las ventas |

**¿Qué valores son buenos?**
- MAE: Mientras más bajo, mejor
- R²: Cerca de 1 es mejor. > 0.7 se considera bueno

---

### ¿Por qué un modelo por producto?

Cada producto tiene patrones de venta **diferentes**:
- El pan francés vende más los domingos
- Los medialunas venden más los lunes
- Los pasteles aumentan en fechas especiales

Un solo modelo no capturaría estas diferencias. Por eso entrenamos **un Random Forest por cada producto**.

---

## 3️⃣ predictor.py - ¿Cómo predecimos?

### Una vez entrenado el modelo, ¿cómo usarlo?

```python
import joblib

def predecir_demanda(producto_id, fecha):
    # 1. Cargar el modelo entrenado
    modelo = joblib.load(f"models_trained/{producto_id}.pkl")
    
    # 2. Obtener las features para la fecha a predecir
    features = construir_features_para_fecha(fecha)
    # result: [dia_semana=2, mes=4, temp=22, condicion=1, ...]
    
    # 3. PREDECIR
    demanda_predicha = modelo.predict([features])[0]
    
    # 4. Redondear a número entero
    return int(round(demanda_predicha))
```

### Para generar predicciones de varios días

```python
def generar_predicciones(n_dias=7):
    hoy = date.today()
    
    for dia in range(n_dias):
        fecha = hoy + timedelta(days=dia)
        
        for producto in lista_productos:
            demanda = predecir_demanda(producto.id, fecha)
            
            # Guardar en la base de datos
            guardar_prediccion(
                producto_id=producto.id,
                fecha_proyectada=fecha,
                demanda_estimada=demanda
            )
```

---

## 4️⃣ weather_api.py - ¿De dónde viene el clima?

### Open-Meteo API

Es un servicio gratuito que da el clima histórico y forecast.

```python
import requests

def obtener_clima_pacasmayo(dias=7):
    # Pacasmayo, La Libertad, Perú
    latitud = -7.2394
    longitud = -79.5699
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitud,
        "longitude": longitud,
        "daily": "temperature_2m_max,temperature_2m_min,weathercode",
        "forecast_days": dias
    }
    
    respuesta = requests.get(url, params=params)
    datos = respuesta.json()
    
    # Transformar a formato de nuestra base de datos
    for i, dia in enumerate(datos["daily"]["time"]):
        insertar_en_base_de_datos(
            fecha=dia,
            temperatura_promedio=(datos["daily"]["temperature_2m_max"][i] + 
                                  datos["daily"]["temperature_2m_min"][i]) / 2,
            condicion=traducir_codigo_clima(datos["daily"]["weathercode"][i])
        )
```

---

## 5️⃣ seed_data.py - Datos de ejemplo

### ¿Por qué necesitamos datos de prueba?

Para que el modelo funcione, necesita **historial de ventas**. El script `seed_data.py` genera:
- 7 productos (panadería y repostería)
- 90 días de ventas históricas
- Datos de clima para esos días
- Insumos y proveedores
- Recetas (fichas técnicas)

### Cómo se generan las ventas (patrones realistas)

```python
# Ejemplo de lógica para generar ventas realistas
def generar_venta_dia(producto, fecha):
    base = 100  # venta base
    
    # Factor día de la semana
    if fecha.weekday() == 6:  # Domingo
        base *= 1.3  # 30% más
    elif fecha.weekday() == 0:  # Lunes
        base *= 0.7  # 30% menos
    
    # Factor clima
    if clima == "Lluvia":
        base *= 0.8  # 20% menos
    
    # Factor mes
    if fecha.month == 12:  # Diciembre
        base *= 1.2  # 20% más por navidad
    
    return agregar_ruido(base)  # Añadir variación aleatoria
```

---

## 📊 Resumen: ¿Cómo funciona todo junto?

```
┌─────────────────────────────────────────────────────────────────────┐
│                    1. ENTRENAMIENTO (histórico)                    │
└─────────────────────────────────────────────────────────────────────┘

     Ventas          Clima            Calendario
       │               │                   │
       ▼               ▼                   ▼
   ┌─────────────────────────────────────────────┐
   │              features.py                     │
   │  (convierte fechas → números)               │
   └─────────────────────────────────────────────┘
                    │
                    ▼
   ┌─────────────────────────────────────────────┐
   │              trainer.py                      │
   │  (entrena Random Forest)                    │
   │  → guarda: models_trained/{id}.pkl           │
   └─────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    2. PREDICCIÓN (futuro)                           │
└─────────────────────────────────────────────────────────────────────┘

   Pronóstico      Fecha objetivo          Calendario
   del clima           │                        │
       │               ▼                        │
       ▼        ┌─────────────────────────────────┐
   ┌────────────┤        predictor.py           │
   │            │  (carga modelo + predice)      │
   └────────────┤  → demanda_estimada           │
                └─────────────────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ FactPrediccion      │
              │ (se guarda en BD)   │
              └─────────────────────┘
```

---

## 🎓 Conceptos clave resumidos

| Concepto | Explicación simple |
|----------|-------------------|
| **Feature** | Una variable de entrada (como "temperatura" o "día de la semana") |
| **Target** | Lo que queremos predecir (ventas del día) |
| **Entrenar** | Enseñar al modelo con datos históricos |
| **Predecir** | Usar el modelo para datos nuevos |
| **Modelo** | Archivo que guarda lo aprendido (ej: 7.pkl) |
| **Random Forest** | Algoritmo que promedia muchos árboles de decisión |
| **MAE** | Error promedio en unidades |
| **R²** | Qué tan bien explica las variaciones (0-1) |

---

## 🚀 Cómo usar

### 1. Entrenar todos los modelos
```python
# Llamar al endpoint
POST /ml/entrenar
```

### 2. Generar predicciones
```python
# Predecir los próximos 7 días
POST /predicciones/generar?n_dias=7
```

### 3. Ver predicciones
```python
GET /predicciones/
```

---

*Documentación del Módulo ML - Sistema Predictivo Panadería Victoria*