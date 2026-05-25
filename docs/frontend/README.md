# 📱 Documentación del Frontend - Sistema Predictivo Panadería Victoria

> Guía completa de la interfaz de usuario construida con Streamlit.

---

## 📁 Estructura del Frontend

```
frontend/
├── app.py                 # Dashboard principal
├── pages/                 # Páginas adicionales
│   ├── 1_Predicciones.py      # Predicciones de demanda
│   ├── 2_Analisis_Mermas.py   # Análisis de mermas
│   ├── 3_Inventario.py        # Gestión de inventario
│   ├── 4_Ordenes_Compra.py    # Órdenes de reposición
│   ├── 5_Modelo_ML.py         # Entrenamiento de modelos
│   ├── 6_Registro_Diario.py   # Registro de ventas
│   └── 7_Reportes_Financieros.py  # Reportes financieros
└── pages/                 # (configuración de Streamlit)
```

---

## 🎯 ¿Qué es Streamlit?

**Streamlit** es un framework de Python para crear interfaces web interactivas sin saber HTML/CSS.

Características:
- ✅ Escribir solo Python
- ✅ Actualización automática al guardar
- ✅ Componentes interactivos (botones, filtros, gráficos)
- ✅ Integración nativa con Pandas y Plotly

---

## 🚀 Cómo ejecutar el frontend

### Desde la carpeta `frontend`:

```bash
cd frontend
streamlit run app.py
```

### O con puerto específico:

```bash
streamlit run app.py --server.port 8501
```

### Abrir en navegador:
```
http://localhost:8501
```

---

## 📱 Navegación

### Sidebar (Menú lateral)

El menú lateral aparece automáticamente y contiene:

```
┌─────────────────────────────┐
│ 🥖 Panadería Victoria       │
│ Sistema Predictivo IA       │
│ ─────────────────────────── │
│ Navegación                  │
│ • 🏠 Dashboard              │
│ • 📈 Predicciones           │
│ • 📊 Mermas                 │
│ • 🏪 Inventario             │
│ • 🛒 Órdenes                │
│ • 🤖 Modelo ML             │
│ • ✏️ Registro              │
│ ─────────────────────────── │
│ API: localhost:8000        │
│ BD: PostgreSQL             │
└─────────────────────────────┘
```

---

## 📄 Descripción de Cada Página

### 1. Dashboard Principal (`app.py`)

**Propósito**: Vista rápida del estado actual del sistema.

**Componentes**:
- KPI: Ventas de hoy
- KPI: Mermas de hoy
- KPI: Porcentaje de merma (30 días)
- KPI: Insumos en alerta
- Gráfico: Producción sugerida (próximos 7 días)
- Botones de acceso rápido

---

### 2. Predicciones (`1_Predicciones.py`)

**Propósito**: Ver y generar predicciones de demanda.

**Funcionalidades**:
- Botón "Generar nuevas predicciones" → llama al modelo ML
- Botón "Sincronizar clima" → trae datos de Open-Meteo
- Gráfico de barras: demanda por producto (próximos 7 días)
- Tabla detallada: producto, fecha, unidades, confianza del modelo
- Gráfico circular: distribución de producción semanal
- Filtro: seleccionar productos a visualizar

---

### 3. Análisis de Mermas (`2_Analisis_Mermas.py`)

**Propósito**: Diagnosticar las causas de pérdida de productos.

**Componentes**:
- KPI: Porcentaje de merma global (con comparación a meta de 20%)
- KPI: Total de unidades perdidas
- KPI: Merma por sobreproducción vs otras causas
- Gráfico de pastel: mermas por motivo
- Gráfico de barras: mermas por producto
- Tabla: últimas 20 mermas registradas

---

### 4. Gestión de Inventario (`3_Inventario.py`)

**Propósito**: Controlar el stock de insumos críticos.

**Componentes**:
- Sección de productos: precio de venta, costo, margen
- KPI: Total de insumos
- KPI: Stock OK
- KPI: Bajo stock mínimo (alertas)
- Gráficos de barras: estado de stock por insumo
- Expansor por insumo: proveedor, stock actual, stock mínimo
- Formulario para actualizar stock manualmente

---

### 5. Órdenes de Compra (`4_Ordenes_Compra.py`)

**Propósito**: Gestionar órdenes de reposición de insumos.

**Pestañas**:
1. **Ver órdenes**: tabla con todas las órdenes, filtros por estado
2. **Crear orden**: formulario para nueva orden

**Estados de orden**:
- 🟡 Pendiente
- 🟢 Recibido
- 🔴 Cancelado

---

### 6. Modelo ML (`5_Modelo_ML.py`)

**Propósito**: Entrenar y evaluar los modelos predictivos.

**Funcionalidades**:
- Listado de productos con estado de entrenamiento
- Botón para entrenar un modelo específico
- Botón para entrenar todos los modelos
- Métricas mostradas: MAE, R²
- Comparación: predicciones vs ventas reales (gráfico)
- Indicador visual de modelo listo/no listo

---

### 7. Registro Diario (`6_Registro_Diario.py`)

**Propósito**: Registrar ventas, producción y mermas diarias.

**Pestañas**:
1. **Registro de ventas**: formulario para nueva venta
2. **Historial**: tabla de ventas registradas
3. **Cargar datos de prueba**: botón para generar datos示例

**Automático**:
- Al registrar venta, si producción > venta, se crea merma automáticamente

---

### 8. Reportes Financieros (`7_Reportes_Financieros.py`)

**Propósito**: Análisis económico del negocio.

**Filtros**:
- Selector de fecha inicio
- Selector de fecha fin
- Botón para actualizar reporte

**Componentes**:
- KPIs: Ingresos totales, Costo producción, Pérdida por merma, Utilidad bruta
- Gráfico: Ingresos por producto
- Gráfico: Evolución de ingresos
- Tabla detallada por producto
- Botón para exportar a PDF

---

## 🎨 Estilo Visual

### Colores utilizados

| Elemento | Color |
|----------|-------|
| Fondo principal | `#0f1117` (negro oscuro) |
| Fondo de tarjetas | `#1e2a3a` (azul oscuro) |
| Bordes | `#2d4a6a` (azul grisáceo) |
| Texto principal | `#e2e8f0` (blanco suave) |
| Acento principal | `#ff6b35` (naranja) |
| Éxito | `#34d399` (verde) |
| Error/Peligro | `#f87171` (rojo) |
| Advertencia | `#f59e0b` (amarillo/naranja) |

### Tipografía

- **Fuente**: Inter (Google Fonts)
- **Tamaños**:
  - Títulos: 1.5rem - 2rem
  - Cuerpo: 0.85rem - 1rem
  - KPI values: 2rem

---

## 🔌 Integración con el Backend

### Cómo se comunica

El frontend usa la librería `requests` para llamar a la API:

```python
import requests

API = "http://localhost:8000"

# GET - Obtener datos
productos = requests.get(f"{API}/productos/").json()

# POST - Enviar datos
nueva_venta = {
    "producto_id": 1,
    "fecha": "2024-01-15",
    "cantidad_vendida": 100,
    "cantidad_producida": 120
}
requests.post(f"{API}/ventas/", json=nueva_venta)
```

### Endpoints más usados

| Página | Endpoints usados |
|--------|-----------------|
| Dashboard | `/dashboard/resumen` |
| Predicciones | `/predicciones/`, `/predicciones/generar`, `/clima/sincronizar` |
| Mermas | `/mermas/`, `/mermas/analisis` |
| Inventario | `/insumos/`, `/insumos/alertas/`, `/productos/` |
| Órdenes | `/ordenes-compra/`, `/proveedores/`, `/insumos/` |
| Modelo ML | `/ml/entrenar`, `/predicciones/vs-real` |
| Registro | `/ventas/`, `/productos/`, `/seed-data/cargar` |
| Reportes | `/ventas/`, `/mermas/`, `/productos/` |

---

## 🛠️ Componentes de Streamlit常用

### Mostrar datos

```python
# Tabla interactiva
st.dataframe(df, use_container_width=True)

# Métrica con indicador
st.metric("Ventas", "150", delta="+10%", delta_color="normal")
```

### Gráficos

```python
# Gráfico de barras (Plotly)
fig = px.bar(df, x="producto", y="ventas")
st.plotly_chart(fig, use_container_width=True)

# Gráfico de líneas
fig = px.line(df, x="fecha", y="ventas")
st.plotly_chart(fig)

# Gráfico circular
fig = px.pie(df, values="ventas", names="producto")
st.plotly_chart(fig)
```

### Formularios

```python
# Campos de entrada
nombre = st.text_input("Nombre:")
precio = st.number_input("Precio:", min_value=0.0)
fecha = st.date_input("Fecha:")
opcion = st.selectbox("Producto:", lista_productos)
```

### Botones

```python
if st.button("Guardar"):
    # Acción al hacer clic
    pass

if st.download_button("Descargar", datos, "archivo.csv"):
    # Descargar archivo
    pass
```

---

## 📊 Librerías Usadas

| Librería | Uso |
|----------|-----|
| `streamlit` | Interfaz de usuario |
| `requests` | Llamadas a la API del backend |
| `pandas` | Manipulación de datos |
| `plotly.express` | Gráficos interactivos |
| `plotly.graph_objects` | Gráficos avanzados |
| `datetime` | Fechas |
| `xhtml2pdf` | Exportar a PDF |

---

## ⚠️ Manejo de Errores

El frontend maneja errores comunes así:

```python
try:
    datos = requests.get(f"{API}/recurso/").json()
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
```

También verifica códigos de estado:

```python
r = requests.get(f"{API}/recurso/")
if r.status_code == 200:
    datos = r.json()
else:
    st.error(f"Error del servidor: {r.status_code}")
```

---

## 🔧 Personalización

### Cambiar el título de la página

```python
st.set_page_config(
    page_title="Mi Título",
    page_icon="🥖",
    layout="wide"
)
```

### Agregar CSS personalizado

```python
st.markdown("""
<style>
.mi-clase {
    color: #ff6b35;
}
</style>
""", unsafe_allow_html=True)
```

### Crear columnas

```python
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("A", "100")
with col2:
    st.metric("B", "200")
```

---

## 📝 Glosario de Términos

| Término | Significado |
|---------|-------------|
| **Streamlit** | Framework para crear UI web con Python |
| **KPI** | Indicador clave de rendimiento (Key Performance Indicator) |
| **Endpoint** | URL de la API que realiza una acción |
| **Pandas DataFrame** | Estructura de datos tabular |
| **Plotly** | Librería para crear gráficos interactivos |
| **Callback** | Función que se ejecuta al interactuar con un componente |

---

*Documentación del Frontend - Sistema Predictivo Panadería Victoria*