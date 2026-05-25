# 📡 Documentación de Endpoints de la API

> Referencia completa de todos los endpoints disponibles en el backend.

---

## 📍 Información General

- **Base URL**: `http://localhost:8000`
- **Documentación interactiva**: `http://localhost:8000/docs` (Swagger UI)
- **Versión actual**: 2.0

---

## 📦 Productos

### Listar todos los productos
```http
GET /productos/
```
**Respuesta:**
```json
[
  {
    "id": 1,
    "nombre": "Pan francés",
    "categoria": "Panadería",
    "precio": 1.50,
    "costo": 0.80
  },
  {
    "id": 2,
    "nombre": "Medialuna",
    "categoria": "Panadería",
    "precio": 1.20,
    "costo": 0.60
  }
]
```

---

### Crear un producto
```http
POST /productos/
```

**Body:**
```json
{
  "nombre": "Croissant",
  "categoria": "Pasteleria",
  "precio": 2.50,
  "costo": 1.20
}
```

---

### Obtener un producto específico
```http
GET /productos/{id}
```

---

### Actualizar un producto
```http
PUT /productos/{id}
```

**Body (enviar solo los campos a cambiar):**
```json
{
  "precio": 1.80
}
```

---

### Eliminar un producto
```http
DELETE /productos/{id}
```

---

## 💰 Ventas

### Listar todas las ventas
```http
GET /ventas/
```
**Respuesta:**
```json
[
  {
    "id": 1,
    "producto_id": 1,
    "producto_nombre": "Pan francés",
    "fecha": "2024-01-15",
    "cantidad_vendida": 120,
    "cantidad_producida": 150
  }
]
```

---

### Registrar una venta
```http
POST /ventas/
```

**Body:**
```json
{
  "producto_id": 1,
  "fecha": "2024-01-15",
  "cantidad_vendida": 120,
  "cantidad_producida": 150
}
```

**⚠️ Importante**: Si `cantidad_producida > cantidad_vendida`, se crea automáticamente una merma con motivo "Sobreproducción".

---

### Eliminar una venta
```http
DELETE /ventas/{id}
```

Al eliminar, también se elimina la merma automática asociada.

---

## 📉 Mermas

### Listar todas las mermas
```http
GET /mermas/
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "producto_id": 1,
    "producto_nombre": "Pan francés",
    "fecha": "2024-01-15",
    "cantidad_merma": 30,
    "motivo": "Sobreproducción"
  }
]
```

---

### Registrar una merma
```http
POST /mermas/
```

**Body:**
```json
{
  "producto_id": 1,
  "fecha": "2024-01-15",
  "cantidad_merma": 10,
  "motivo": "Vencido"
}
```

---

### Análisis de mermas
```http
GET /mermas/analisis
```

**Respuesta:**
```json
{
  "porcentaje_merma_global": 5.2,
  "total_unidades_merma": 1250,
  "por_motivo": [
    {"motivo": "Sobreproducción", "frecuencia": 45, "total_merma": 800},
    {"motivo": "Vencido", "frecuencia": 20, "total_merma": 300},
    {"motivo": "Daño", "frecuencia": 5, "total_merma": 150}
  ],
  "por_producto": [
    {"producto": "Pan francés", "total_merma": 500, "frecuencia": 30},
    {"producto": "Medialuna", "total_merma": 350, "frecuencia": 25}
  ]
}
```

---

## 🏭 Insumos

### Listar todos los insumos
```http
GET /insumos/
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "nombre": "Harina de trigo",
    "stock_actual": 50.0,
    "stock_minimo": 100.0,
    "unidad_medida": "Kg",
    "proveedor_id": 1
  }
]
```

---

### Crear un insumo
```http
POST /insumos/
```

**Body:**
```json
{
  "nombre": "Mantequilla",
  "stock_actual": 20,
  "stock_minimo": 30,
  "unidad_medida": "Kg",
  "proveedor_id": 2
}
```

---

### Actualizar stock de insumo
```http
PUT /insumos/{id}
```

**Body:**
```json
{
  "stock_actual": 80
}
```

---

### Ver alertas de insumos (bajo stock)
```http
GET /insumos/alertas/
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "nombre": "Harina de trigo",
    "stock_actual": 50,
    "stock_minimo": 100,
    "unidad_medida": "Kg",
    "necesita_reorden": true,
    "proveedor_id": 1
  }
]
```

---

## 🌤️ Clima

### Listar datos de clima
```http
GET /clima/
```

---

### Agregar dato de clima
```http
POST /clima/
```

**Body:**
```json
{
  "fecha": "2024-01-15",
  "temperatura_promedio": 22.5,
  "condicion": "Soleado",
  "es_feriado": false,
  "evento_especial": null
}
```

---

### Sincronizar clima desde Open-Meteo
```http
POST /clima/sincronizar?dias=7
```

**Respuesta:**
```json
{
  "registros_insertados": 5,
  "registros_actualizados": 2
}
```

---

## 🤖 Machine Learning

### Entrenar modelos
```http
POST /ml/entrenar?producto_id=1
```

**Respuesta:**
```json
{
  "producto_id": 1,
  "producto_nombre": "Pan francés",
  "mae": 5.2,
  "r2": 0.85,
  "muestras_entrenamiento": 90
}
```

Para entrenar todos los productos:
```http
POST /ml/entrenar
```

---

### Generar predicciones
```http
POST /predicciones/generar?n_dias=7
```

**Respuesta:**
```json
{
  "total_predicciones": 21,
  "mensaje": "Predicciones generadas para los próximos 7 días"
}
```

---

### Listar predicciones
```http
GET /predicciones/
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "producto_id": 1,
    "producto_nombre": "Pan francés",
    "fecha_proyectada": "2024-01-16",
    "demanda_estimada": 125.0,
    "confianza_prediccion": 0.85
  }
]
```

---

### Comparar predicciones vs ventas reales
```http
GET /predicciones/vs-real?dias=30
```

**Respuesta:**
```json
{
  "predicciones_vs_reales": [
    {
      "fecha": "2024-01-15",
      "producto": "Pan francés",
      "predicho": 120,
      "real": 115,
      "error": 5,
      "error_porcentaje": 4.3
    }
  ],
  "precision_promedio": 0.88
}
```

---

## 🛒 Órdenes de Compra

### Listar órdenes
```http
GET /ordenes-compra/
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "proveedor_nombre": "Molinos del Norte",
    "insumo_nombre": "Harina de trigo",
    "fecha_orden": "2024-01-10",
    "cantidad": 100,
    "precio_unitario": 0.85,
    "estado": "pendiente"
  }
]
```

---

### Crear orden de compra
```http
POST /ordenes-compra/
```

**Body:**
```json
{
  "proveedor_id": 1,
  "insumo_id": 1,
  "fecha_orden": "2024-01-10",
  "cantidad": 100,
  "precio_unitario": 0.85,
  "estado": "pendiente"
}
```

---

### Actualizar estado de orden
```http
PUT /ordenes-compra/{id}/estado?estado=recibido
```

Estados posibles: `pendiente`, `recibido`, `cancelado`

---

## 📊 Proveedores

### Listar proveedores
```http
GET /proveedores/
```

---

### Crear proveedor
```http
POST /proveedores/
```

**Body:**
```json
{
  "nombre": "Distribuidora de Azúcar",
  "contacto": "Juan Pérez",
  "telefono": "999-888-777",
  "email": "juan@distriazucar.com"
}
```

---

## 📋 Fichas Técnicas (Recetas)

### Listar fichas técnicas
```http
GET /fichas-tecnicas/
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "producto_nombre": "Pan francés",
    "insumo_nombre": "Harina de trigo",
    "cantidad_necesaria": 0.25
  }
]
```

---

### Crear ficha técnica
```http
POST /fichas-tecnicas/
```

**Body:**
```json
{
  "producto_id": 1,
  "insumo_id": 1,
  "cantidad_necesaria": 0.25
}
```

---

## 🖥️ Dashboard y Sistema

### Estado del sistema
```http
GET /sistema/estado
```

**Respuesta:**
```json
{
  "base_de_datos": {
    "productos": 7,
    "ventas": 450,
    "insumos": 12,
    "alertas_stock": 3
  },
  "machine_learning": {
    "total_productos": 7,
    "modelos_listos": 7,
    "todos_entrenados": true
  }
}
```

---

### Resumen del dashboard
```http
GET /dashboard/resumen
```

---

## 📄Tabla de Referencia Rápida

| Recurso | GET | POST | PUT | DELETE |
|---------|-----|------|-----|--------|
| Productos | `/productos/` | `/productos/` | `/productos/{id}` | `/productos/{id}` |
| Ventas | `/ventas/` | `/ventas/` | - | `/ventas/{id}` |
| Mermas | `/mermas/` | `/mermas/` | - | - |
| Insumos | `/insumos/` | `/insumos/` | `/insumos/{id}` | - |
| Clima | `/clima/` | `/clima/` | - | - |
| Predicciones | `/predicciones/` | `/predicciones/generar` | - | - |
| Órdenes | `/ordenes-compra/` | `/ordenes-compra/` | `/ordenes-compra/{id}/estado` | - |
| Proveedores | `/proveedores/` | `/proveedores/` | - | - |
| Fichas Técnicas | `/fichas-tecnicas/` | `/fichas-tecnicas/` | - | - |

---

*Documentación de Endpoints - Sistema Predictivo Panadería Victoria*