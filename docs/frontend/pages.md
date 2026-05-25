# 📄 Guía Detallada de Páginas del Frontend

> Explicación paso a paso de cada página del sistema.

---

## 📑 Índice de Página

1. [Dashboard Principal](#1-dashboard-principal)
2. [Predicciones](#2-predicciones)
3. [Análisis de Mermas](#3-análisis-de-mermas)
4. [Gestión de Inventario](#4-gestión-de-inventario)
5. [Órdenes de Compra](#5-órdenes-de-compra)
6. [Modelo ML](#6-modelo-ml)
7. [Registro Diario](#7-registro-diario)
8. [Reportes Financieros](#8-reportes-financieros)

---

## 1️⃣ Dashboard Principal (`app.py`)

### ¿Qué muestra?

Es la **página de inicio** que da una visión general del estado del sistema.

### Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│  VENTAS HOY          MERMAS HOY        % MERMA (30D)    INSUMOS│
│    245 uds             15 uds              5.2%            3      │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────┐ ┌──────────────────────────────┐
│  🔮 PRODUCCIÓN SUGERIDA       │ │  📋 RESUMEN DE OPERACIONES   │
│  (Gráfico de barras)          │ │  Órdenes pendientes: 2       │
│                              │ │  Fecha actual: 29/04/2026    │
│  Pan francés: ████ 120       │ │                              │
│  Medialuna:  ███   90       │ │  [Ir a Registro Diario]      │
│  Croissant:  ██    60       │ │  [Ver Reportes]              │
└──────────────────────────────┘ └──────────────────────────────┘
```

### Código clave

```python
# Obtener datos del backend
resumen = requests.get(f"{API}/dashboard/resumen").json()

# Mostrar métricas
col1.metric("Ventas Hoy", f"{resumen['ventas_hoy']:.0f} uds")

# Mostrar gráfico
st.bar_chart(df_p.set_index('producto'))
```

---

## 2️⃣ Predicciones (`1_Predicciones.py`)

### Propósito
Mostrar las predicciones de demanda generadas por el modelo ML y permitir generar nuevas.

### Flujo

```
1. Usuario hace clic en "Generar nuevas predicciones"
   → POST /predicciones/generar?n_dias=7
   → Backend ejecuta el modelo y guarda predicciones

2. Backend devuelve: {total_predicciones: 21}

3. Frontend muestra:
   - Gráfico de barras agrupado (hoy vs mañana)
   - Tabla con detalle por producto y fecha
   - Gráfico circular de distribución semanal
```

### Características

- ✅ Filtro por productos (multiselect)
- ✅ Gráfico con traducción de días a español
- ✅ Porcentaje de confianza del modelo

### Variables mostradas

| Campo | Descripción |
|-------|-------------|
| Producto | Nombre del producto |
| Fecha | Fecha proyectada (con día en español) |
| Unidades Estimadas | Cantidad predicha |
| Confianza Modelo | Porcentaje de precisión (R²) |

---

## 3️⃣ Análisis de Mermas (`2_Analisis_Mermas.py`)

### Propósito
Diagnosticar el nivel de mermas y sus causas raíz (Objetivo Específico 1).

### KPIs mostrados

```
┌─────────────────┬──────────────────┬────────────────────┐
│ % MERMA GLOBAL │ TOTAL MERMA (uds) │ MERMA SOBREPROD.   │
│     5.2%        │      1,250        │      850 (68%)     │
│ Meta: ≤20%      │                  │                    │
└─────────────────┴──────────────────┴────────────────────┘
```

### Gráficos

1. **Porcentaje de merma global**: Comparación con meta (línea roja en 20%)
2. **Por motivo**: Pie chart de causas (Sobreproducción, Vencido, Daño)
3. **Por producto**: Barras horizontales de pérdida por producto
4. **Tabla final**: Últimas 20 mermas registradas

### Motivos de merma

- **Sobreproducción**: Se produjo más de lo que se vendió
- **Vencido**: El producto no se vendió a tiempo
- **Daño**: Producto dañado o contaminado

---

## 4️⃣ Gestión de Inventario (`3_Inventario.py`)

### Propósito
Controlar el stock de insumos críticos y alertar cuando falta inventario.

### Sección 1: Productos

Muestra una tabla con todos los productos:

| Producto | Categoría | Precio Venta | Costo | Margen % |
|----------|-----------|--------------|-------|----------|
| Pan francés | Panadería | S/ 1.50 | S/ 0.80 | 87.5% |
| Medialuna | Panadería | S/ 1.20 | S/ 0.60 | 100% |

### Sección 2: Insumos

```
┌─────────────────────────────────────────────────────────────────┐
│ Total Insumos: 12    Stock OK: 9    Bajo Stock Mínimo: 3 🚨     │
└─────────────────────────────────────────────────────────────────┘

▼ Harina de trigo — 50 / 100 Kg  🔴
    [Gráfico de barras horizontal]
    Proveedor: Molinos del Norte
    Déficit: 50 Kg
```

### Estado de stock

- 🟢 **OK**: stock_actual ≥ stock_minimo
- 🔴 **Alerta**: stock_actual < stock_minimo

### Formulario de actualización

```python
sel = st.selectbox("Seleccionar insumo:", lista_insumos)
nuevo_stock = st.number_input("Nuevo stock:")
if st.button("Actualizar"):
    PUT /insumos/{id} → {"stock_actual": nuevo_stock}
```

---

## 5️⃣ Órdenes de Compra (`4_Ordenes_Compra.py`)

### Propósito
Gestionar órdenes de reposición de insumos.

### Pestañas

#### Pestaña 1: Ver órdenes

```
┌─────────────────────────────────────────────────────────────────┐
│ Total órdenes: 15    Pendientes: 3    Recibidas: 12             │
├─────────────────────────────────────────────────────────────────┤
│ FILTRO: [Todos ▼]                                              │
├─────────────────────────────────────────────────────────────────┤
│ Proveedor      │ Insumo      │ Fecha    │ Cantidad │ Estado    │
│ Molinos Norte │ Harina      │ 15/01/24 │ 100 kg   │ 🟢 Recibido│
│ Distri Azúcar  │ Azúcar      │ 20/01/24 │ 50 kg    │ 🟡 Pendiente│
└─────────────────────────────────────────────────────────────────┘
```

#### Pestaña 2: Crear orden

```
┌─────────────────────────────────────────────────────────────────┐
│ PROVEEDOR: [Molinos del Norte ▼]                               │
│ INSUMO:     [Harina de trigo ▼]                                 │
│ FECHA:      [📅 29/04/2026]                                     │
│ CANTIDAD:   [100]                                               │
│ PRECIO:     [S/ 0.85]                                           │
│ ESTADO:     [Pendiente ▼]                                       │
├─────────────────────────────────────────────────────────────────┤
│                     [Crear Orden]                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6️⃣ Modelo ML (`5_Modelo_ML.py`)

### Propósito
Entrenar los modelos Random Forest y ver métricas de rendimiento.

### Vista principal

```
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 MODELOS DE MACHINE LEARNING                                  │
│                                                                  │
│ │ Producto          │ Estado        │ MAE    │ R²    │ Acción   │
│ ├───────────────────┼───────────────┼────────┼───────┼─────────┤
│ │ Pan francés       │ ✅ Listo      │ 5.2    │ 0.85  │ [Ver]    │
│ │ Medialuna         │ ✅ Listo      │ 3.8    │ 0.82  │ [Ver]    │
│ │ Croissant        │ ⏳ Entrenando  │ -      │ -     │ [Train]  │
└─────────────────────────────────────────────────────────────────┘

[Entrenar Todos los Modelos]
```

### Métricas explicadas

| Métrica | Significado | Valores típicos |
|---------|-------------|-----------------|
| **MAE** | Error absoluto medio (unidades) | < 10 es bueno |
| **R²** | Precisión del modelo (0-1) | > 0.7 es bueno |

### Comparación Predicciones vs Reales

```
Predicción vs Real (Últimos 30 días)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Predicho  ───●─────────────
Real      ──────●─────────

Precisión promedio: 88%
```

---

## 7️⃣ Registro Diario (`6_Registro_Diario.py`)

### Propósito
Registrar las ventas, producción y mermas diarias.

### Pestañas

#### Pestaña 1: Registro de ventas

```
┌─────────────────────────────────────────────────────────────────┐
│ NUEVA VENTA                                                     │
├─────────────────────────────────────────────────────────────────┤
│ PRODUCTO:     [Pan francés ▼]                                   │
│ FECHA:        [📅 29/04/2026]                                   │
│ CANT. VENDIDA: [120]                                            │
│ CANT. PRODUCIDA:[150]                                           │ ← Si > venda, crea merma auto
│ MOTIVO MERMA:  [Sobreproducción ▼] (si aplica)                 │
├─────────────────────────────────────────────────────────────────┤
│                     [Registrar Venta]                          │
└─────────────────────────────────────────────────────────────────┘
```

#### Pestaña 2: Historial

Tabla con todas las ventas registradas, con opción de eliminar.

```
│ Fecha     │ Producto   │ Vendido │ Producido │ Merma Auto │
│ 29/04/24  │ Pan francés│  120    │   150     │     30     │
│ 29/04/24  │ Medialuna  │   85    │    80     │     -      │
```

#### Pestaña 3: Cargar datos de ejemplo

Botón para generar 90 días de datos de prueba (ventas, clima, mermas).

---

## 8️⃣ Reportes Financieros (`7_Reportes_Financieros.py`)

### Propósito
Análisis económico: ingresos, costos y pérdidas por merma.

### Filtros de fecha

```
┌─────────────────────────────────────────────────────────────────┐
│ DESDE: [📅 01/01/2024]   HASTA: [📅 31/03/2024]   [🔄 Actualizar]│
└─────────────────────────────────────────────────────────────────┘
```

### KPIs financieros

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ INGRESOS    │ COSTO PROD.  │ PÉRDIDA MERMA│ UTILIDAD    │
│  S/ 45,230  │  S/ 18,500   │   S/ 2,100   │  S/ 24,630   │
│   TOTALES    │              │              │   BRUTA     │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

### Fórmulas

```
Ingreso = cantidad_vendida × precio_producto
Costo Producción = cantidad_producida × costo_producto
Pérdida Merma = cantidad_merma × costo_producto
Utilidad Bruta = Ingresos - Costo Producción
```

### Gráficos

1. **Ingresos por producto** (barras horizontales)
2. **Evolución de ingresos** (línea temporal)

### Tabla detallada

| Producto | Uds Vendidas | Ingreso | Costo Prod | Pérdida Merma | Margen |
|----------|--------------|---------|------------|---------------|--------|
| Pan francés | 5,000 | S/ 7,500 | S/ 4,000 | S/ 500 | S/ 3,000 |

### Exportar a PDF

Botón que genera un PDF con:
- Período del reporte
- KPIs
- Gráficos embebidos
- Tabla detallada

---

## 🔄 Resumen de Flujos de Datos

### Flujo 1: Registrar venta

```
Frontend: form → POST /ventas/
Backend: validar, guardar en FactVenta
         si produccion > venta → crear FactMerma
Backend: return {id, ...}
Frontend: mostrar éxito, recargar tabla
```

### Flujo 2: Generar predicciones

```
Frontend: botón → POST /predicciones/generar?n_dias=7
Backend: para cada producto:
         - cargar modelo entrenado
         - predecir demanda para cada día
         - guardar en FactPrediccion
Backend: return {total_predicciones: 21}
Frontend: mostrar gráfico y tabla
```

### Flujo 3: Ver reportes

```
Frontend: seleccionar fechas → GET /ventas/, GET /mermas/
Backend: return datos
Frontend: calcular KPIs, mostrar gráficos
         botón PDF → generar HTML → convertir a PDF
         st.download_button()
```

---

*Guía de Páginas del Frontend - Sistema Predictivo Panadería Victoria*