# 📚 Documentación del Backend - Sistema Predictivo Panadería Victoria

> Documentación detallada para principiantes. Cada sección explica **qué hace** y **cómo funciona**.

---

## 📁 Estructura del Proyecto

```
backend/
├── main.py           # API principal con FastAPI (TODOS los endpoints)
├── database.py       # Conexión a PostgreSQL
├── models.py         # Definición de tablas de la base de datos
├── reset_db.py       # Script para reiniciar la base de datos
└── ml/               # Módulo de Machine Learning
    ├── trainer.py    # Entrenamiento del modelo Random Forest
    ├── predictor.py  # Generación de predicciones
    ├── features.py   # Ingeniería de características (variables)
    ├── weather_api.py# Integración con API de clima
    └── seed_data.py  # Datos de ejemplo para pruebas
```

---

## 🔧 1. database.py - Conexión a la Base de Datos

### ¿Qué hace?
Establece la conexión con PostgreSQL, la base de datos donde se guarda toda la información.

### Código explicado

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

# Carga las credenciales desde el archivo .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# URL de la base de datos (definida en .env)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://eduardo:123456@localhost:5432/panaderia_victoria"
)

# Crear el motor de conexión
engine = create_engine(DATABASE_URL)

# Crear sesiones para hacer consultas
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para definir las tablas
Base = declarative_base()

# Función para obtener una sesión (usada en cada endpoint)
def get_db():
    db = SessionLocal()
    try:
        yield db  # Retorna la sesión
    finally:
        db.close()  # Siempre cierra la sesión al terminar
```

### ¿Para qué sirve cada parte?

| Código | Para qué sirve |
|--------|----------------|
| `create_engine` | Conecta Python con PostgreSQL |
| `SessionLocal` | Crea "sesiones" para hacer operaciones en la BD |
| `Base` | Clase base para definir las tablas |
| `get_db()` | Función que cada endpoint usa para acceder a la BD |

---

## 🗄️ 2. models.py - Estructura de las Tablas

### ¿Qué hace?
Define todas las tablas de la base de datos usando SQLAlchemy (ORM).

### Concepto clave: Tablas tipo "Dimensión" y "Hecho"

- **Dimensiones** = "Qué" (Productos, Insumos, Proveedores, Clima)
- **Hechos** = "Qué pasó" (Ventas, Mermas, Predicciones, Órdenes)

---

### 2.1 DimProducto (Productos que vende la panadería)

```python
class DimProducto(Base):
    __tablename__ = "dim_productos"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(255))        # Ej: "Pan francés"
    categoria = Column(String(100))     # Ej: "Panadería"
    precio = Column(Float)              # Precio de venta al cliente
    costo = Column(Float)              # Costo de producción
```

**Relaciones**: Un producto tiene muchas ventas, mermas, predicciones.

---

### 2.2 DimClima (Condiciones climáticas)

```python
class DimClima(Base):
    __tablename__ = "dim_clima"

    fecha = Column(Date, primary_key=True)
    temperatura_promedio = Column(Float)  # Ej: 22.5°C
    condicion = Column(String(50))       # Soleado, Nublado, Lluvia
    es_feriado = Column(Boolean)         # True/False
    evento_especial = Column(String(100)) # "Día de la Madre", "Navidad"
```

**¿Por qué?** El modelo ML usa el clima para predecir ventas.

---

### 2.3 Proveedor (Empresas que venden insumos)

```python
class Proveedor(Base):
    __tablename__ = "dim_proveedores"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(255))    # Ej: "Molinos del Norte"
    contacto = Column(String(255))  # Nombre del contacto
    telefono = Column(String(50))   # Teléfono
    email = Column(String(255))     # Correo electrónico
```

---

### 2.4 InsumoCritico (Materias primas)

```python
class InsumoCritico(Base):
    __tablename__ = "insumos_criticos"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(255))        # Ej: "Harina de trigo"
    stock_actual = Column(Float)        # Cuánto hay ahora
    stock_minimo = Column(Float)        # Cuánto es el mínimo antes de reordenar
    unidad_medida = Column(String(50))  # "Kg", "Litros", "Unidades"
    proveedor_id = Column(Integer, ForeignKey("dim_proveedores.id"))
```

---

### 2.5 FichaTecnica (Recetas - Tabla intermedia)

```python
class FichaTecnica(Base):
    __tablename__ = "fichas_tecnicas"

    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey("dim_productos.id"))
    insumo_id = Column(Integer, ForeignKey("insumos_criticos.id"))
    cantidad_necesaria = Column(Float)  # Cuánto insumo se necesita por unidad
```

**Ejemplo**: 1 Pan francés = 0.25 kg de harina.

---

### 2.6 FactVenta (Registros de ventas diarias)

```python
class FactVenta(Base):
    __tablename__ = "fact_ventas"

    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey("dim_productos.id"))
    fecha = Column(Date)                    # Fecha de la venta
    cantidad_vendida = Column(Float)       # Cuántas unidades se vendieron
    cantidad_producida = Column(Float)     # Cuántas se produjeron (para calcular merma)
```

---

### 2.7 FactMerma (Productos perdidos/botados)

```python
class FactMerma(Base):
    __tablename__ = "fact_mermas"

    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey("dim_productos.id"))
    venta_id = Column(Integer, ForeignKey("fact_ventas.id"))  # Venta asociada
    fecha = Column(Date)
    cantidad_merma = Column(Float)         # Cuántas unidades se perdieron
    motivo = Column(String(255))           # "Sobreproducción", "Vencido", etc.
```

---

### 2.8 FactPrediccion (Predicciones del modelo ML)

```python
class FactPrediccion(Base):
    __tablename__ = "fact_predicciones"

    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey("dim_productos.id"))
    fecha_proyectada = Column(Date)        # Fecha para la predicción
    demanda_estimada = Column(Float)       # Cuántas unidades se predice vender
    confianza_prediccion = Column(Float)    # Precisión del modelo (0-1)
```

---

### 2.9 OrdenCompra (Órdenes de reposición)

```python
class OrdenCompra(Base):
    __tablename__ = "fact_ordenes_compra"

    id = Column(Integer, primary_key=True)
    proveedor_id = Column(Integer, ForeignKey("dim_proveedores.id"))
    insumo_id = Column(Integer, ForeignKey("insumos_criticos.id"))
    fecha_orden = Column(Date)
    cantidad = Column(Float)
    precio_unitario = Column(Float)        # Precio por unidad
    estado = Column(String(50))            # "pendiente", "recibido", "cancelado"
```

---

## 🌐 3. main.py - API con FastAPI

### ¿Qué es FastAPI?
Es un framework para crear APIs web en Python. Permite que otras aplicaciones (como Streamlit) reciban y envíen datos.

### Estructura de un endpoint

```python
@app.get("/ruta/del endpoint")  # Define la URL
def nombre_de_la_funcion(parametros):
    # Código que se ejecuta cuando alguien llama a esta URL
    return {"respuesta": "datos"}
```

---

### Endpoints disponibles

#### 📍 Raíz
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Verifica que la API está activa |

```python
@app.get("/")
def read_root():
    return {
        "status": "online",
        "version": "2.0",
        "mensaje": "Sistema Predictivo Panadería Victoria — API activa"
    }
```

---

#### 📦 Productos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/productos/` | Listar todos los productos |
| POST | `/productos/` | Crear un nuevo producto |
| GET | `/productos/{id}` | Ver un producto específico |
| PUT | `/productos/{id}` | Actualizar un producto |
| DELETE | `/productos/{id}` | Eliminar un producto |

**Ejemplo de uso**:
- GET `/productos/` → `[{id: 1, nombre: "Pan francés", precio: 1.50}]`
- POST `/productos/` → `{nombre: "Croissant", categoria: "Pasteleria", precio: 2.50, costo: 1.00}`

---

#### 💰 Ventas

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/ventas/` | Listar todas las ventas |
| POST | `/ventas/` | Registrar una venta |
| DELETE | `/ventas/{id}` | Eliminar una venta |

**Automático**: Al registrar una venta, si `cantidad_producida > cantidad_vendida`, se crea automáticamente una merma.

---

#### 📉 Mermas

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/mermas/` | Listar todas las mermas |
| POST | `/mermas/` | Registrar una merma |
| GET | `/mermas/analisis` | Ver estadísticas de mermas |

**Análisis incluye**:
- Porcentaje de merma global
- Mermas por motivo (Sobreproducción, Vencido, etc.)
- Mermas por producto

---

#### 🏭 Insumos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/insumos/` | Listar todos los insumos |
| POST | `/insumos/` | Crear un insumo |
| PUT | `/insumos/{id}` | Actualizar insumo |
| GET | `/insumos/alertas/` | Ver insumos que necesitan reorder |
| POST | `/clima/sincronizar` | Importar clima desde Open-Meteo |

---

#### 🌤️ Clima

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/clima/` | Ver todos los datos de clima |
| POST | `/clima/` | Agregar dato de clima |
| POST | `/clima/sincronizar?dias=7` | Traer clima de los próximos 7 días |

---

#### 🤖 Machine Learning

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/ml/entrenar` | Entrenar los modelos Random Forest |
| POST | `/predicciones/generar?n_dias=7` | Generar predicciones para próximos N días |
| GET | `/predicciones/` | Ver predicciones generadas |
| GET | `/predicciones/vs-real` | Comparar predicciones vs ventas reales |

---

#### 🛒 Órdenes de Compra

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/ordenes-compra/` | Listar todas las órdenes |
| POST | `/ordenes-compra/` | Crear una orden |
| PUT | `/ordenes-compra/{id}/estado?estado=nuevo_estado` | Cambiar estado |

Estados posibles: `pendiente`, `recibido`, `cancelado`

---

#### 📊 Dashboard

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/sistema/estado` | Ver estado general del sistema |
| GET | `/dashboard/resumen` | Resumen rápido para el frontend |

---

### Schemas (Modelos de datos)

Los schemas definen qué datos se esperan en cada request/response.

```python
# Schema para crear un producto
class ProductoCreate(BaseModel):
    nombre: str
    categoria: str
    precio: float
    costo: float

# Schema de respuesta (incluye el ID)
class ProductoResponse(ProductoCreate):
    id: int
    class Config:
        from_attributes = True
```

---

## 🤖 4. Módulo ML - Machine Learning

### Flujo completo

```
┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│ 1. DATOS     │───▶│ 2. ENTRENAR │───▶│ 3. PREDECIR │
│ (Ventas +    │    │ (Random     │    │ (Predecir   │
│  Clima)       │    │  Forest)    │    │  demanda)   │
└──────────────┘    └─────────────┘    └──────────────┘
```

---

### 4.1 features.py - Ingeniería de características

**¿Qué hace?** Prepara los datos para que el modelo pueda aprender.

**Variables que usa el modelo**:

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `dia_semana` | Temporal | 0=Lunes, 6=Domingo |
| `mes` | Temporal | 1-12 |
| `dia_mes` | Temporal | 1-31 |
| `dia_anio` | Temporal | 1-365 |
| `es_finde` | Temporal | 1 si es sábado/domingo |
| `temperatura_promedio` | Clima | Grados Celsius |
| `condicion` | Clima | Soleado, Nublado, Lluvia |
| `es_feriado` | Calendario | True/False |
| `evento_especial` | Calendario | "Día de la Madre", "Navidad" |
| `ventas_lag_1` | Histórico | Ventas de ayer |
| `ventas_lag_7` | Histórico | Ventas de hace 7 días |
| `ventas_rolling_7` | Histórico | Promedio últimos 7 días |

---

### 4.2 trainer.py - Entrenamiento del modelo

**¿Qué hace?** Entrena un modelo Random Forest para cada producto.

```python
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

def entrenar_modelo(producto_id):
    # 1. Cargar datos de ventas y clima
    df = cargar_datos_desde_db()
    
    # 2. Filtrar por producto
    df_prod = df[df['producto_id'] == producto_id]
    
    # 3. Construir features
    X, y = get_X_y(df_prod)
    
    # 4. Dividir en entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X, y)
    
    # 5. Crear y entrenar el modelo
    modelo = RandomForestRegressor(n_estimators=100)
    modelo.fit(X_train, y_train)
    
    # 6. Evaluar
    predicciones = modelo.predict(X_test)
    mae = mean_absolute_error(y_test, predicciones)
    r2 = r2_score(y_test, predicciones)
    
    # 7. Guardar el modelo
    joblib.dump(modelo, f"models_trained/{producto_id}.pkl")
    
    return {"mae": mae, "r2": r2}
```

**Métricas**:
- **MAE** (Mean Absolute Error): Error promedio en unidades
- **R²**: Porcentaje de variación explicada (0-1)

---

### 4.3 predictor.py - Generar predicciones

**¿Qué hace?** Usa los modelos entrenados para predecir ventas futuras.

```python
def generar_predicciones(n_dias=7):
    # Para cada producto
    for producto_id in lista_productos:
        # Cargar modelo
        modelo = joblib.load(f"models_trained/{producto_id}.pkl")
        
        # Para cada día futuro
        for dia in range(n_dias):
            fecha = fecha_hoy + dia
            
            # Obtener features para esa fecha (clima, día, etc.)
            features = construir_features(fecha)
            
            # Predecir
            demanda = modelo.predict([features])[0]
            
            # Guardar en la base de datos
            crear_prediccion(producto_id, fecha, demanda)
```

---

### 4.4 weather_api.py - Integración con Open-Meteo

**¿Qué hace?** Descarga el clima real/pronosticado desde internet.

```python
import requests

def obtener_clima(latitud, longitud, dias):
    url = f"https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitud,
        "longitude": longitud,
        "daily": "temperature_2m_max,weathercode",
        "forecast_days": dias
    }
    response = requests.get(url, params=params)
    return response.json()
```

---

### 4.5 seed_data.py - Datos de prueba

**¿Qué hace?** Genera datos de ejemplo para probar el sistema.

Incluye:
- 7 productos (panes, reposterías)
- Proveedores de harina, azúcar, levadura
- Insumos críticos (harina, azúcar, mantequilla, etc.)
- 90 días de ventas históricas con patrones realistas
- Datos de clima para esos 90 días
- Recetas (fichas técnicas)

---

## 🔄 5. Flujo de Datos Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FLUJO DEL SISTEMA                               │
└─────────────────────────────────────────────────────────────────────┘

1. REGISTRO DIARIO
   └─> Usuario registra: ventas, producción, mermas
       └─> Se guarda en: FactVenta, FactMerma

2. SINCRONIZACIÓN DE CLIMA
   └─> Se conecta a Open-Meteo API
       └─> Se guarda en: DimClima

3. ENTRENAMIENTO DEL MODELO
   └─> Carga: ventas + clima + calendario
       └─> Procesa: features.py
       └─> Entrena: trainer.py (Random Forest)
       └─> Guarda: modelos en models_trained/*.pkl

4. GENERACIÓN DE PREDICCIONES
   └─> Para cada producto: usa modelo entrenado
       └─> Predice demanda para próximos N días
       └─> Guarda en: FactPrediccion

5. ANÁLISIS DE MERMAS
   └─> Compara: producción vs ventas
       └─> Detecta: sobreproducción (producción > ventas)
       └─> Registra: FactMerma

6. ALERTAS DE INVENTARIO
   └─> Compara: stock_actual vs stock_minimo
       └─> Si stock_actual < stock_minimo → ALERTA

7. ÓRDENES DE COMPRA
   └─> Usuario crea orden manualmente
       └─> Se guarda en: OrdenCompra

8. DASHBOARD (Streamlit)
   └─> Lee: todas las tablas
       └─> Muestra: gráficos, tablas, KPIs
```

---

## 📋 6. Resumen de Tablas

| Tabla | Tipo | Descripción |
|-------|------|-------------|
| `dim_productos` | Dimensión | Productos que vende la panadería |
| `dim_clima` | Dimensión | Datos climáticos por fecha |
| `dim_proveedores` | Dimensión | Empresas proveedoras |
| `insumos_criticos` | Dimensión | Materias primas |
| `fichas_tecnicas` | Intermedia | Recetas (producto → insumo) |
| `fact_ventas` | Hecho | Ventas diarias registradas |
| `fact_mermas` | Hecho | Productos perdidos |
| `fact_predicciones` | Hecho | Predicciones del modelo ML |
| `fact_ordenes_compra` | Hecho | Órdenes de compra de insumos |

---

## 🚀 7. Cómo ejecutar

### Iniciar el backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Ver la documentación automática
Abre en tu navegador: `http://localhost:8000/docs`

---

## 📝 Glosario de términos

| Término | Significado |
|---------|-------------|
| **API** | Interfaz de programación - permite que aplicaciones se comuniquen |
| **Endpoint** | Una URL específica que hace una acción (ej: GET /productos/) |
| **ORM** | Object-Relational Mapping - forma de usar Python con bases de datos |
| **Random Forest** | Algoritmo de ML que usa muchos árboles de decisión |
| **Feature** | Variable de entrada para el modelo |
| **Train** | Entrenar - enseñar al modelo con datos históricos |
| **Predict** | Predecir - usar el modelo para obtener resultados futuros |
| **Schema** | Estructura que define qué datos se esperan |
| **Dependency Injection** | Patrón para pasar la sesión de BD a cada endpoint |

---

*Documentación creada para el proyecto de Tesis - Sistema Predictivo de Producción para Panadería Victoria*