# 📚 Documentación del Frontend - Índice

> Documentación completa de la interfaz de usuario Streamlit.

---

## 📂 Archivos de Documentación

| Archivo | Descripción |
|---------|-------------|
| **[README.md](README.md)** | Visión general, estructura, cómo ejecutar, componentes de Streamlit |
| **[pages.md](pages.md)** | Guía detallada de cada página del sistema |

---

## 🎯 Resumen

El **Frontend** es la interfaz gráfica que permite a los usuarios interactuar con el sistema sin necesidad de conocer código.

### Tecnologías usadas
- **Streamlit**: Framework para crear la interfaz web
- **Plotly**: Gráficos interactivos
- **Pandas**: Manipulación de datos
- **Requests**: Comunicación con el backend

### Cómo iniciar

```bash
cd frontend
streamlit run app.py
```

Luego abrir: `http://localhost:8501`

---

## 📋 Descripción de las 8 Páginas

| # | Página | Archivo | Propósito |
|---|--------|---------|-----------|
| 1 | Dashboard | `app.py` | Vista rápida del estado del sistema |
| 2 | Predicciones | `1_Predicciones.py` | Ver y generar predicciones ML |
| 3 | Análisis de Mermas | `2_Analisis_Mermas.py` | Diagnosticar causas de pérdida |
| 4 | Inventario | `3_Inventario.py` | Controlar stock de insumos |
| 5 | Órdenes de Compra | `4_Ordenes_Compra.py` | Gestionar reposición |
| 6 | Modelo ML | `5_Modelo_ML.py` | Entrenar y evaluar modelos |
| 7 | Registro Diario | `6_Registro_Diario.py` | Registrar ventas y producción |
| 8 | Reportes Financieros | `7_Reportes_Financieros.py` | Análisis económico con PDF |

---

## 🔗 Conexión Frontend ↔ Backend

```
┌─────────────────┐        ┌─────────────────┐
│    FRONTEND    │───────▶│    BACKEND     │
│   (Streamlit)   │◀───────│   (FastAPI)    │
└─────────────────┘        └─────────────────┘
        │                         │
        ▼                         ▼
   Usuario ve              PostgreSQL
   gráficos                datos
```

El frontend hace **llamadas HTTP** al backend:
- `GET /recurso/` → Obtener datos
- `POST /recurso/` → Crear datos
- `PUT /recurso/{id}` → Actualizar
- `DELETE /recurso/{id}` → Eliminar

---

*Documentación Frontend - Sistema Predictivo Panadería Victoria*