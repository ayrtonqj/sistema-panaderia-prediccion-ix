# Sistema Predictivo de Produccion — Panaderia Victoria

**Sistema de prediccion de demanda y automatizacion de cadena de suministro basado en Machine Learning para reduccion de mermas en una panaderia.**

> Proyecto de Tesis — Universidad Nacional de Trujillo (UNT), Escuela de Ingenieria, 2026-I
> Pacasmayo, La Libertad, Peru

---

## Tabla de Contenidos

1. [Descripcion del Proyecto](#descripcion-del-proyecto)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Stack Tecnologico Detallado](#stack-tecnologico-detallado)
4. [Modelos de Machine Learning](#modelos-de-machine-learning)
5. [Base de Datos: Esquema Completo](#base-de-datos-esquema-completo)
6. [Credenciales y Accesos](#credenciales-y-accesos)
7. [Variables de Entorno](#variables-de-entorno)
8. [API Endpoints](#api-endpoints)
9. [Instalacion y Despliegue](#instalacion-y-despliegue)
10. [Automatizacion con n8n (OE4)](#automatizacion-con-n8n-oe4)
11. [Chatbot con Ollama](#chatbot-con-ollama)
12. [Estructura del Proyecto](#estructura-del-proyecto)
13. [Testing](#testing)
14. [Referencias para Articulo Cientifico](#referencias-para-articulo-cientifico)

---

## Descripcion del Proyecto

Sistema predictivo que utiliza algoritmos de Machine Learning para predecir la demanda diaria de productos de panaderia, considerando variables climaticas, calendario de eventos y patrones historicos de ventas. El sistema automatiza la cadena de suministro mediante flujos de trabajo n8n y proporciona dashboards interactivos para la toma de decisiones.

**Objetivo principal:** Reducir las mermas de produccion en al menos 20% mediante predicciones precisas y automatizacion de la cadena de suministro.

### Caracteristicas principales

- Prediccion de demanda con 7 algoritmos ML (seleccion automatica del mejor por producto)
- Integracion climatica via API Open-Meteo (Pacasmayo, Peru)
- Dashboard web con visualizacion de KPIs, graficos y exportacion a PDF/Excel
- Automatizacion de ordenes de compra via n8n
- Autenticacion con 2FA (TOTP via Google Authenticator)
- Chatbot con IA (Ollama + llama3.2) para consultas del sistema
- Notificaciones por email (Gmail SMTP) y Telegram
- Sistema de roles: administrador, gerente, cocina, vendedor

---

## Arquitectura del Sistema

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                DOCKER COMPOSE                                     │
│                                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐ │
│  │  PostgreSQL   │    │   pgAdmin    │    │     n8n      │    │  Backend FastAPI  │ │
│  │    :5432      │    │   :8080      │    │   :5678      │    │     :8000         │ │
│  │  (Datos del   │    │  (Admin DB)  │    │  (Workflow    │    │  (API + ML +     │ │
│  │   sistema)    │    │              │    │   autom.)     │    │   Chatbot)       │ │
│  └──────┬───────┘    └──────────────┘    └──────┬───────┘    └────────┬─────────┘ │
│         │                                       │                     │           │
│         └───────────────────────────────────────┼─────────────────────┘           │
│                                                 │                                 │
│  ┌──────────────────────────────────────────────┴──────────────────────────────┐  │
│  │                           Frontend React (Vite)                             │  │
│  │                               :80 (prod) / :5173 (dev)                     │  │
│  │             18 paginas, Chart.js, html2pdf, xlsx, nginx                     │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────┘
              │                              │
              ▼                              ▼
     ┌──────────────┐              ┌──────────────────────┐
     │  Open-Meteo   │              │  Ollama (local)     │
     │  (Clima API)  │              │  llama3.2           │
     │  Sin API key  │              │  :11434             │
     └──────────────┘              └──────────────────────┘
```

### Flujo de datos

1. **Ventas diarias** → Registradas por vendedores via frontend o API
2. **Datos climaticos** → Sincronizados automaticamente desde Open-Meteo para Pacasmayo (-7.4006, -79.5714)
3. **Ingenieria de features** → Construccion de 13 variables predictoras (lags, medias moviles, dummies)
4. **Entrenamiento** → 7 algoritmos evaluados por producto, se selecciona el mejor por RMSE
5. **Prediccion** → Generacion de demanda estimada para los proximos N dias
6. **Alertas de insumos** → Deteccion de stock bajo minimo y sugerencia de ordenes de compra
7. **Automatizacion** → n8n ejecuta workflow diario a las 8:00 AM para crear ordenes automaticas
8. **Notificaciones** → Email y Telegram ante alertas criticas

---

## Stack Tecnologico Detallado

### Backend (Python)

| Componente | Tecnologia | Version | Proposito |
|------------|-----------|---------|-----------|
| Framework web | FastAPI | >=0.100.0 | API RESTful asincrona |
| Servidor ASGI | Uvicorn | >=0.23.0 | Servidor web |
| ORM | SQLAlchemy | >=2.0.0 | Mapeo objeto-relacional |
| Conector DB | psycopg2-binary | >=2.9.0 | Conexion PostgreSQL |
| Validacion | Pydantic | >=2.0.0 | Schemas y validacion |
| Auth JWT | python-jose | >=3.3.0 | Tokens de sesion |
| Hashing | passlib[bcrypt] | >=1.7.0 | Hash de contrasenas |
| 2FA | pyotp + qrcode | — | TOTP con Google Authenticator |
| Cifrado | cryptography (Fernet) | >=41.0.0 | Cifrado de datos sensibles |
| HTTP | httpx / aiohttp / requests | varias | Clientes HTTP |
| Programacion | APScheduler | — | Tareas programadas |
| Testing | pytest | >=7.4.0 | Pruebas unitarias |

### Machine Learning / Data Science

| Componente | Tecnologia | Version | Proposito |
|------------|-----------|---------|-----------|
| Computacion cientifica | numpy | >=1.24.0 | Algebra lineal |
| DataFrames | pandas | >=2.0.0 | Manipulacion de datos |
| ML clasico | scikit-learn | >=1.3.0 | Algoritmos de ML |
| Series temporales | statsmodels | >=0.14.0 | ARIMA/SARIMA |
| Forecasting | prophet | >=1.1.0 | Prophet (Meta) |
| Serializacion | joblib | >=1.3.0 | Guardar/cargar modelos .pkl |

### Frontend (React + Vite)

| Componente | Tecnologia | Version | Proposito |
|------------|-----------|---------|-----------|
| Framework UI | React | ^19.2.6 | Interfaz de usuario |
| Build tool | Vite | ^8.0.12 | Bundler y dev server |
| Graficos | Chart.js | ^4.5.1 | Visualizacion de datos |
| React-Chartjs | react-chartjs-2 | ^5.3.1 | Integracion Chart.js+React |
| Exportacion PDF | html2pdf.js | ^0.14.0 | Generacion de PDF |
| Exportacion Excel | xlsx | ^0.18.5 | Generacion de Excel |
| Linter | ESLint | ^10.3.0 | Calidad de codigo |
| Proxy dev | Vite proxy | — | Proxy a backend :8000 |

### Frontend: Paginas (18 modulos)

| Pagina | Archivo | Funcion |
|--------|---------|---------|
| Login | `LoginPage.jsx` | Autenticacion + 2FA |
| Dashboard | `DashboardPage.jsx` | KPIs generales y graficos |
| Catalogo | `CatalogoPage.jsx` | CRUD productos |
| Vendedores | `VendedoresPage.jsx` | CRUD vendedores |
| Venta Rapida | `VentaRapidaPage.jsx` | Registro rapido de ventas |
| Registro Diario | `RegistroDiarioPage.jsx` | Registro de produccion |
| Control Perdidas | `ControlPerdidasPage.jsx` | Gestion de mermas |
| Inventario | `InventarioPage.jsx` | Gestion de insumos |
| Proveedores | `ProveedoresPage.jsx` | CRUD proveedores |
| Ordenes Compra | `OrdenesCompraPage.jsx` | Ordenes de compra |
| Predicciones | `PrediccionesPage.jsx` | Visualizar predicciones |
| Modelo Estadistico | `ModeloEstadisticoPage.jsx` | Comparacion de modelos |
| Reportes Financieros | `ReportesFinancierosPage.jsx` | Reportes contables |
| Anomalias | `AnomaliasPage.jsx` | Deteccion de anomalias |
| Pan Pasado | `PanPasadoPage.jsx` | Gestion de pan del dia anterior |
| Podios | `PodiosPage.jsx` | Rankings de productos/vendedores |
| Notificaciones | `NotificacionesPage.jsx` | Configuracion de alertas |
| Seguridad | `SecurityPage.jsx` | Configuracion 2FA |

### Infraestructura y Servicios

| Componente | Tecnologia | Proposito |
|------------|-----------|-----------|
| Contenedores | Docker + Docker Compose | Orquestacion de servicios |
| Base de datos | PostgreSQL 15 | Almacenamiento persistente |
| Admin DB | pgAdmin 4 (dpage/pgadmin4) | Interfaz grafica de BD |
| Automatizacion | n8n (n8nio/n8n) | Workflows automaticos |
| Proxy frontend | nginx:alpine | Servir SPA en produccion |
| Chatbot local | Ollama + llama3.2 | Asistente virtual |

### Servicios Externos

| Servicio | URL | API Key | Uso |
|----------|-----|---------|-----|
| Open-Meteo | `https://api.open-meteo.com/v1/forecast` | No requiere | Datos climaticos de Pacasmayo |
| Telegram Bot | `https://api.telegram.org/bot{token}/sendMessage` | Variable `TELEGRAM_BOT_TOKEN` | Notificaciones |
| Gmail SMTP | `smtp.gmail.com:587` | App password en `.env` | Envio de reportes por email |

---

## Modelos de Machine Learning

### Algoritmos implementados (7)

| # | Algoritmo | Libreria | Tipo | Hiperparametros clave |
|---|-----------|----------|------|----------------------|
| 1 | Random Forest | scikit-learn | Ensemble (bagging) | n_estimators=200, max_depth=8, min_samples_leaf=3 |
| 2 | Linear Regression | scikit-learn | Modelo lineal | Sin hiperparametros (OLS) |
| 3 | Gradient Boosting | scikit-learn | Ensemble (boosting) | n_estimators=150, max_depth=5, learning_rate=0.08 |
| 4 | ARIMA | statsmodels | Series temporales | order=(1,0,1), fallback (1,0,0) |
| 5 | Prophet | prophet (Meta) | Descomposicion | weekly_seasonality=True, seasonality_mode='multiplicative' |
| 6 | MLP Neural Network | scikit-learn | Red neuronal | hidden_layer_sizes=(64,32), activation='relu', solver='adam' |
| 7 | Ensemble (RF+GB+LR) | scikit-learn | Votacion ponderada | Pesos: RF=2, GB=2, LR=1 |

### Feature Engineering (13 variables)

Las siguientes variables se construyen a partir de ventas historicas y datos climaticos en `backend/ml/features.py`:

1. `lag_1` — Ventas del dia anterior
2. `lag_2` — Ventas de hace 2 dias
3. `lag_3` — Ventas de hace 3 dias
4. `lag_7` — Ventas de hace 7 dias (misma semana)
5. `rolling_3` — Media movil de 3 dias
6. `rolling_7` — Media movil de 7 dias
7. `rolling_14` — Media movil de 14 dias
8. `rolling_30` — Media movil de 30 dias
9. `dia_semana` — Dia de la semana (0=domingo, ..., 6=sabado)
10. `es_domingo` — Variable dummy para domingo
11. `es_sabado` — Variable dummy para sabado
12. `temperatura` — Temperatura promedio del dia (de dim_clima)
13. `es_feriado` — Variable dummy para feriados

### Arquitectura de entrenamiento

- **24 productos** cada uno con su propio modelo individual
- **Seleccion automatica**: Se entrena los 7 algoritmos por producto y se selecciona el de menor RMSE
- **Particion**: Train (ultimos 60+ dias), Test (ultimos 30 dias)
- **Metricas**: MAE, RMSE, R²
- **Persistencia**: Modelos guardados como `.pkl` con joblib en `backend/ml/models_trained/`
- **Meta-datos**: Cada modelo guarda su `best_{id}_meta.json` con metricas e hiperparametros
- **Mapping global**: `best_model.json` mapea cada producto al mejor algoritmo

### Archivos de modelos entrenados

```
backend/ml/models_trained/
├── best_model.json                    # Mapping producto -> mejor algoritmo
├── best_1.pkl ... best_24.pkl         # Mejor modelo por producto
├── best_1_meta.json ... best_24_meta.json  # Metricas del mejor modelo
├── model_random_forest_1.pkl ...      # Todos los modelos RF (24)
├── model_linear_regression_1.pkl ...  # Todos los modelos LR (24)
├── model_gradient_boosting_1.pkl ...  # Todos los modelos GB (24)
├── model_mlp_neural_network_1.pkl ... # Todos los modelos MLP (24)
├── model_arima_1.pkl ...              # Todos los modelos ARIMA (24)
├── model_sarima_1.pkl ...             # Todos los modelos SARIMA (24)
├── model_ensemble_rfplusgbpluslr_1.pkl ... # Todos los Ensemble (24)
└── legacy_backup/                     # Backup de versiones anteriores
```

---

## Base de Datos: Esquema Completo

### Modelo: Estrella (Star Schema)

**6 tablas de dimension (contexto) + 6 tablas de hechos (transacciones) + 2 tablas intermedias = 14 tablas**

### Dimensiones

| Tabla | Descripcion | Campos clave |
|-------|-------------|-------------|
| `dim_vendedores` | Vendedores/empleados | id, nombre, apellido, dni, telefono, email, username, password, activo |
| `dim_productos` | Catalogo de productos | id, nombre (255 chars), categoria, precio, costo |
| `dim_clima` | Datos climaticos diarios | fecha (PK), temperatura_promedio, condicion, es_feriado, evento_especial |
| `dim_proveedores` | Proveedores de insumos | id, nombre, contacto, telefono, email |
| `insumos_criticos` | Insumos/inventario | id, nombre, stock_actual, stock_minimo, unidad_medida, proveedor_id (FK) |
| `totp_config` | Configuracion 2FA | username (PK), totp_secret, totp_enabled, old_totp_secret |

### Hechos

| Tabla | Descripcion | Medidas | Foreign Keys |
|-------|-------------|---------|--------------|
| `fact_ventas` | Ventas diarias | cantidad_vendida, precio_unitario | producto_id, vendedor_id |
| `fact_mermas` | Perdidas/mermas | cantidad_merma, motivo | producto_id |
| `fact_produccion` | Produccion diaria | cantidad_producida | producto_id |
| `fact_predicciones` | Predicciones ML | demanda_estimada, confianza_prediccion, algoritmo_utilizado | producto_id |
| `fact_ordenes_compra` | Ordenes a proveedores | cantidad, precio_unitario, estado, es_sugerida | proveedor_id, insumo_id |
| `pan_pasado` | Pan del dia anterior | cantidad, precio_unitario, cantidad_vendida, estado | producto_id |

### Tablas intermedias

| Tabla | Descripcion |
|-------|-------------|
| `fichas_tecnicas` | Recetas: producto_id -> insumo_id + cantidad_necesaria |
| `proveedores_insumos` | Precios por proveedor: proveedor_id + insumo_id + precio_unitario |

### Diagrama de relaciones

```
dim_vendedores ──< fact_ventas >── dim_productos ──< fact_mermas
                                                       │
dim_clima (fecha) ── (usada en features ML)            │
                                                       │
dim_proveedores ──< insumos_criticos >── fichas_tecnicas >── dim_productos
       │                                                  │
       └──< proveedores_insumos >── insumos_criticos      │
                                                          │
fact_ordenes_compra >── dim_proveedores                    │
       └──< insumos_criticos                               │
                                                          │
fact_predicciones >── dim_productos                        │
                                                          │
fact_produccion >── dim_productos                         │
                                                          │
pan_pasado >── dim_productos                              │
                                                          │
totp_config (independiente, key=username)                 │
```

---

## Credenciales y Accesos

### Servicios del sistema

| Servicio | URL | Usuario | Contrasena |
|----------|-----|---------|------------|
| **PostgreSQL** | `localhost:5432` | `eduardo` | `123456` |
| **pgAdmin** | `http://localhost:8080` | `admin@tesis.com` | `admin` |
| **n8n** | `http://localhost:5678` | `admin` | `admin123` |
| **Backend API** | `http://localhost:8000` | — | — |
| **Swagger Docs** | `http://localhost:8000/docs` | — | — |
| **Frontend (React)** | `http://localhost:80` (prod) / `http://localhost:5173` (dev) | — | — |

### Roles de usuario del sistema

| Rol | Username | Password | Descripcion |
|-----|----------|----------|-------------|
| Administrador | `admin` | `administrador` | Acceso total al sistema |
| Gerente | `gerente` | `gerente` | Reportes y supervision |
| Cocina | `cocina` | `cocina` | Gestion de produccion |
| Vendedor 1 | `vendedor01` | `vendedor123` | Registro de ventas (Josue Angeldones) |
| Vendedor 2 | `vendedor02` | `vendedor456` | Registro de ventas (Eduardo Quinones) |

### Vendedores por defecto (creados automaticamente al iniciar)

| Nombre | Apellido | DNI | Telefono | Email | Username | Password |
|--------|----------|-----|----------|-------|----------|----------|
| Josue | Angeldones | `12345678` | `999111000` | josue@panaderia.com | `vendedor01` | `vendedor123` |
| Eduardo | Quinones | `87654321` | `999222000` | eduardo@panaderia.com | `vendedor02` | `vendedor456` |

### Servicios de notificacion (GMAIL - ACTIVO)

| Variable | Valor |
|----------|-------|
| SMTP Email | `hendry.angeldones09@gmail.com` |
| SMTP Password (App password) | `khbqtggthebvscrc` |
| Admin Email | `hendry.angeldones09@gmail.com` |
| Servidor SMTP | `smtp.gmail.com:587` (STARTTLS) |

> **ADVERTENCIA**: Las credenciales de GMAIL estan expuestas en el repositorio local. Se recomienda rotar la contrasena de aplicacion de Google y mover `.env` a un gestor de secretos.

---

## Variables de Entorno

### Archivo `.env` (raiz del proyecto)

```env
# === Email (Gmail SMTP) ===
SMTP_EMAIL=hendry.angeldones09@gmail.com
SMTP_PASSWORD=khbqtggthebvscrc
ADMIN_EMAIL=hendry.angeldones09@gmail.com

# === Notificaciones ===
GMAIL_USER=hendry.angeldones09@gmail.com
GMAIL_APP_PASSWORD=khbqtggthebvscrc
```

### Archivo `.env.example` (template para nuevos despliegues)

```env
# Seguridad del backend
SECRET_KEY=cambia-esta-clave-por-una-secreta-larga-y-aleatoria

# Base de datos (usado por el backend)
DATABASE_URL=postgresql://eduardo:123456@db:5432/panaderia_victoria

# Token del bot de Telegram (crear con @BotFather)
TELEGRAM_BOT_TOKEN=

# Gmail SMTP para envio de reportes
GMAIL_USER=tu_correo@gmail.com
GMAIL_APP_PASSWORD=

# Clave de cifrado Fernet para datos sensibles
ENCRYPTION_KEY=
```

### Variables usadas en docker-compose.yml

| Variable | Donde se define | Valor por defecto |
|----------|----------------|-------------------|
| `DATABASE_URL` | `.env`, `docker-compose.yml` | `postgresql://eduardo:123456@db:5432/panaderia_victoria` |
| `SECRET_KEY` | `.env.example`, `docker-compose.yml` | `cambiar-esta-clave-secreta` |
| `TELEGRAM_BOT_TOKEN` | `.env.example`, `docker-compose.yml` | (vacio) |
| `GMAIL_USER` | `.env`, `docker-compose.yml` | `hendry.angeldones09@gmail.com` |
| `GMAIL_APP_PASSWORD` | `.env`, `docker-compose.yml` | `khbqtggthebvscrc` |
| `ENCRYPTION_KEY` | `.env.example`, `docker-compose.yml` | (vacio, se genera automaticamente) |
| `POSTGRES_USER` | `docker-compose.yml` | `eduardo` |
| `POSTGRES_PASSWORD` | `docker-compose.yml` | `123456` |
| `POSTGRES_DB` | `docker-compose.yml` | `panaderia_victoria` |
| `PGADMIN_DEFAULT_EMAIL` | `docker-compose.yml` | `admin@tesis.com` |
| `PGADMIN_DEFAULT_PASSWORD` | `docker-compose.yml` | `admin` |
| `N8N_BASIC_AUTH_USER` | `docker-compose.yml` | `admin` |
| `N8N_BASIC_AUTH_PASSWORD` | `docker-compose.yml` | `admin123` |
| `WEBHOOK_URL` | `docker-compose.yml` | `http://localhost:5678` |

---

## API Endpoints

> Todos los endpoints bajo `http://localhost:8000`. Documentacion Swagger: `http://localhost:8000/docs`

### Autenticacion

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/auth/login` | Inicio de sesion (username + password) |
| POST | `/auth/setup-2fa` | Configurar 2FA (genera QR) |
| POST | `/auth/verify-2fa` | Verificar codigo 2FA |
| POST | `/auth/login-2fa` | Login completo con 2FA |
| POST | `/auth/recover-2fa` | Recuperar 2FA (regenera secreto) |
| POST | `/auth/disable-2fa` | Deshabilitar 2FA |
| GET | `/auth/check` | Verificar sesion activa |

### Productos

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/productos/` | Listar todos los productos |
| GET | `/productos/{id}` | Obtener producto por ID |
| POST | `/productos/` | Crear producto |
| PUT | `/productos/{id}` | Actualizar producto |
| DELETE | `/productos/{id}` | Eliminar producto |

### Vendedores

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/vendedores/` | Listar todos los vendedores |
| GET | `/vendedores/{id}` | Obtener vendedor por ID |
| POST | `/vendedores/` | Crear vendedor |
| PUT | `/vendedores/{id}` | Actualizar vendedor |
| DELETE | `/vendedores/{id}` | Eliminar vendedor |

### Ventas

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/ventas/` | Listar ventas (con filtros) |
| POST | `/ventas/` | Registrar venta individual |
| POST | `/ventas/lote/` | Registrar ventas en lote |
| POST | `/ventas/rapida/` | Venta rapida (datos minimos) |
| GET | `/ventas/resumen` | Resumen de ventas por periodo |

### Produccion

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/produccion/` | Listar registros de produccion |
| POST | `/produccion/` | Registrar produccion |
| POST | `/produccion/sugerir` | Sugerir cantidad a producir basado en predicciones |
| POST | `/produccion/simular` | Simular escenario de produccion |

### Mermas (Perdidas)

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/mermas/` | Listar mermas |
| POST | `/mermas/` | Registrar merma |
| GET | `/mermas/analisis` | Analisis de mermas por motivo/producto |
| DELETE | `/mermas/{id}` | Eliminar registro de merma |
| GET | `/mermas/alertas` | Alertas de mermas elevadas |

### Insumos / Inventario

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/insumos/` | Listar insumos criticos |
| POST | `/insumos/` | Crear insumo |
| PUT | `/insumos/{id}` | Actualizar insumo |
| GET | `/insumos/alertas/` | Insumos bajo stock minimo |
| POST | `/insumos/ajustar-stock` | Ajustar stock manualmente |

### Proveedores

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/proveedores/` | Listar proveedores |
| POST | `/proveedores/` | Crear proveedor |
| PUT | `/proveedores/{id}` | Actualizar proveedor |
| DELETE | `/proveedores/{id}` | Eliminar proveedor |

### Ordenes de Compra

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/ordenes-compra/` | Listar ordenes de compra |
| POST | `/ordenes-compra/` | Crear orden de compra |
| POST | `/ordenes-compra/sugerir/` | Sugerir ordenes (insumos bajo minimo) |
| POST | `/ordenes-compra/urgente/` | Crear orden urgente |
| PUT | `/ordenes-compra/{id}/confirmar` | Confirmar orden |
| PUT | `/ordenes-compra/{id}/cancelar` | Cancelar orden |
| PUT | `/ordenes-compra/{id}/recibir` | Marcar como recibido |

### Predicciones y ML

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/ml/entrenar` | Entrenar/reevaluar todos los modelos |
| GET | `/ml/comparar` | Comparar rendimiento de todos los modelos |
| GET | `/ml/comparar/stream` | Comparacion en tiempo real (SSE) |
| GET | `/ml/metricas` | Metricas de todos los modelos entrenados |
| GET | `/ml/mejores-modelos` | Mejor modelo por producto |
| POST | `/predicciones/generar` | Generar predicciones para proximos N dias |
| GET | `/predicciones/` | Listar predicciones generadas |
| GET | `/predicciones/vs-real` | Comparar predicciones vs ventas reales |
| GET | `/predicciones/recomendaciones` | Recomendaciones basadas en predicciones |

### Clima

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/clima/` | Obtener datos climaticos |
| POST | `/clima/sincronizar` | Sincronizar desde Open-Meteo |

### Dashboard

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/dashboard/resumen` | KPIs generales del sistema |
| GET | `/dashboard/kpi` | KPIs detallados |
| GET | `/dashboard/eficiencia` | Eficiencia de produccion |
| GET | `/dashboard/condiciones` | Condiciones de operacion |
| GET | `/dashboard/podios` | Rankings (productos, vendedores) |

### Reportes

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/reportes/financiero` | Reporte financiero en PDF |
| GET | `/reportes/ventas-diarias` | Reporte de ventas diarias |
| GET | `/reportes/rentabilidad` | Reporte de rentabilidad por producto |
| GET | `/reportes/porcentajes` | Porcentajes de ventas por producto |

### Pan Pasado

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/pan-pasado/` | Listar pan del dia anterior |
| POST | `/pan-pasado/` | Registrar pan pasado |
| POST | `/pan-pasado/generar` | Generar automaticamente del dia anterior |
| POST | `/pan-pasado/{id}/vender` | Registrar venta de pan pasado |

### Sistema

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/sistema/estado` | Estado completo del sistema |
| GET | `/sistema/health` | Health check basico |
| POST | `/datos/semilla` | Cargar datos sinteticos iniciales |

### Chatbot

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/chatbot/pregunta` | Hacer pregunta al chatbot |
| POST | `/chatbot/audio` | Enviar audio para transcripcion |

---

## Instalacion y Despliegue

### Requisitos previos

- Python 3.11+
- Node.js 20+
- Docker y Docker Compose (para despliegue completo)
- Ollama (para chatbot, opcional)

### Opcion 1: Despliegue completo con Docker (recomendado)

```bash
# 1. Clonar el repositorio
git clone <repositorio>
cd panaderia-v2

# 2. Configurar variables de entorno (copiar y editar)
cp .env.example .env
# Editar .env con valores reales

# 3. Levantar todos los servicios
docker-compose up -d

# Esto inicia:
# - PostgreSQL en :5432
# - pgAdmin en :8080
# - n8n en :5678
# - Backend (FastAPI) en :8000
# - Frontend (React + nginx) en :80

# 4. Cargar datos iniciales (usar curl.exe en Windows PowerShell)
curl.exe -X POST http://localhost:8000/datos/semilla
curl.exe -X POST http://localhost:8000/ml/entrenar
curl.exe -X POST "http://localhost:8000/predicciones/generar?n_dias=7"
```

### Opcion 2: Desarrollo local (backend + frontend por separado)

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend (en otra terminal)
cd frontend3
npm install
npm run dev
# El frontend se abre en http://localhost:5173
```

### Servicios Docker individuales

```bash
# Solo base de datos
docker-compose up -d db pgadmin

# Solo backend + base de datos
docker-compose up -d db backend

# Todo el stack
docker-compose up -d
```

### Seed data

```bash
# Cargar datos sinteticos (365 dias)
curl.exe -X POST http://localhost:8000/datos/semilla

# Entrenar modelos
curl.exe -X POST http://localhost:8000/ml/entrenar

# Generar predicciones para 7 dias
curl.exe -X POST "http://localhost:8000/predicciones/generar?n_dias=7"

# Sincronizar clima
curl.exe -X POST "http://localhost:8000/clima/sincronizar?dias=7"
```

### Simulación e Inicialización Completa de Datos del Artículo de Tesis (OE6)

Para desplegar el sistema desde cero en una nueva PC o recrear exactamente los datos calibrados del artículo científico (con un 24.9% de reducción física de mermas, ahorro mensual de ~S/ 850.00 en los últimos 90 días, significancia Diebold-Mariano y análisis de ablación), sigue este flujo secuencial en la terminal:

> [!NOTE]
> **Orden de ejecución y prevención de duplicidad:**
> * **Compilación Docker:** Se recomienda usar `docker-compose up -d --build` para asegurar una construcción limpia del stack.
> * **Requisito previo:** `POST /datos/semilla` debe haberse ejecutado al menos una vez para inicializar el catálogo de productos, insumos, proveedores y recetas en la BD vacía.
> * **No hay duplicación:** `seed_articulo.py` **no duplica datos** porque limpia y elimina automáticamente ventas, mermas, clima u órdenes previas antes de insertar la serie calibrada de 360 días.
> * **Nota PowerShell:** En Windows PowerShell, usa `curl.exe` en lugar de `curl` para evitar que PowerShell invoque el alias interno `Invoke-WebRequest`.

```bash
# 1. Clonar el repositorio y entrar a la carpeta
git clone <URL_DEL_REPOSITORIO>
cd sistema-panaderia-prediccion-ix

# 2. Configurar variables de entorno (copiar y editar si deseas VITE_DEMO_MODE=true)
cp .env.example .env

# 3. Levantar todos los servicios con Docker (compilación limpia)
docker-compose up -d --build

# 4. Cargar catálogo base de productos e insumos (necesario si la BD es nueva)
curl.exe -X POST http://localhost:8000/datos/semilla

# 5. Ejecutar seeder del artículo (Genera los 360 días con patrones realistas, mermas OE6 y 168 órdenes n8n)
docker exec -it backend_tesis python ml/seed_articulo.py

# 6. Entrenar modelos ML y generar metadatos de evaluación (R², RMSE, MAE)
docker exec -it backend_tesis python ml/trainer.py
docker exec -it backend_tesis python ml/generate_models_meta.py

# 7. Generar y guardar predicciones a 7 días en la BD
curl.exe -X POST "http://localhost:8000/predicciones/generar?n_dias=7"

# 8. (Opcional) Realizar experimento de control de Análisis de Ablación de clima
docker exec -it backend_tesis python scratch/ablation_study.py
```

*Nota: Si estás corriendo en un entorno de desarrollo local sin Docker, puedes ejecutar los mismos scripts activando el entorno virtual de la carpeta `backend`: `venv\Scripts\python.exe ml/seed_articulo.py`, `venv\Scripts\python.exe ml/trainer.py`, `venv\Scripts\python.exe ml/generate_models_meta.py` y `venv\Scripts\python.exe scratch/ablation_study.py`.*

### Configuración del Modo Demo (Despliegue Público / Render)

Para desplegar el sistema en entornos de demostración pública (ej. Render, Vercel, Netlify) sin requerir que los visitantes ingresen credenciales manualmente, puedes activar el **Modo Demo**:

Configura las siguientes variables de entorno en la app de Frontend:

```env
# Activa el inicio de sesión automático
VITE_DEMO_MODE=true

# URL de la API backend desplegada en Render (ejemplo)
VITE_API_URL=https://sistema-panaderia-backend.onrender.com

# Opcional: Credenciales de auto-login (por defecto usa el usuario 'admin')
VITE_DEMO_USERNAME=admin
VITE_DEMO_PASSWORD=admin
```

> **Comportamiento durante el despertar del servidor (Render Cold Start):**
> * Al estar activo `VITE_DEMO_MODE=true`, si el servidor backend de Render se encuentra en modo reposo (free tier cold start), la aplicación mostrará automáticamente una **Pantalla de Carga de Modo Demo**.
> * Esta pantalla incluye un contador en tiempo real, número de intentos de reconexión y explicación clara para el visitante de que el backend se está activando (pudiendo tomar entre 1 y 2 minutos).
> * Una vez que el backend responde, se autentica automáticamente como Administrador e ingresa al Dashboard.

### 🌐 Guía de Despliegue en la Nube (Render + Vercel)

#### 🔹 Paso 1: Desplegar el Backend en Render
1. Inicia sesión en [Render Dashboard](https://dashboard.render.com/).
2. **Crear Base de Datos PostgreSQL:**
   - Clic en **New +** ➔ **PostgreSQL**.
   - **Name:** `sistema-panaderia-db`
   - **Database:** `panaderia_victoria`
   - Guarda la base de datos y copia la URL interna o de conexión (`Internal Database URL`).
3. **Crear Servicio Web (Backend):**
   - Clic en **New +** ➔ **Web Service**.
   - Conecta el repositorio GitHub `ayrtonqj/sistema-panaderia-prediccion-ix`.
   - **Name:** `sistema-panaderia-backend`
   - **Root Directory:** `backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Variables de Entorno (Environment Variables):**
     - `DATABASE_URL`: *(Pegar la URL de la BD de Render)*
     - `PYTHON_VERSION`: `3.11.0`
   - Clic en **Create Web Service** y copia la URL pública asignada (ejemplo: `https://sistema-panaderia-backend.onrender.com`).
4. **Inicializar datos en Render (100% Gratuito / Sin necesidad de Shell Terminal):**
   - Como el Plan Free de Render no incluye consola de comandos (Shell), hemos creado un **endpoint todo-en-uno**.
   - Simplemente abre la siguiente URL directamente en tu navegador web (reemplazando con la URL de tu backend en Render):
     ```
     https://sistema-panaderia-backend.onrender.com/datos/inicializar-todo
     ```
   - *(O desde tu terminal local ejecuta: `curl.exe https://sistema-panaderia-backend.onrender.com/datos/inicializar-todo`)*
   - Esto poblará la BD vacía, generará los 360 días de datos de tesis, entrenará los modelos ML y guardará las predicciones automáticamente.

#### 🔹 Paso 2: Desplegar el Frontend en Vercel
1. Inicia sesión en [Vercel Dashboard](https://vercel.com/).
2. Clic en **Add New...** ➔ **Project**.
3. Importa el repositorio `ayrtonqj/sistema-panaderia-prediccion-ix`.
4. Configuración del proyecto:
   - **Framework Preset:** `Vite`
   - **Root Directory:** Haz clic en Edit y selecciona la carpeta `frontend3`.
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. **Variables de Entorno en Vercel (Environment Variables):**
   - `VITE_API_URL`: `https://sistema-panaderia-backend.onrender.com`
   - `VITE_DEMO_MODE`: `true`
6. Clic en **Deploy**. ¡Tu sistema estará en línea y accesible públicamente!

---

## Automatizacion con n8n (OE4)

El workflow de n8n automatiza la creacion de ordenes de compra cuando los insumos estan bajo stock minimo.

### Archivos

| Archivo | Descripcion |
|---------|-------------|
| `n8n-workflow.json` | Definicion del workflow en formato JSON |
| `n8n/setup_n8n_workflow.py` | Script Python para importar workflow en n8n |

### Funcionamiento

1. **Trigger**: Schedule diario a las 8:00 AM
2. **Deteccion**: Consulta `GET /insumos/alertas/` para identificar insumos bajo stock minimo
3. **Accion**: Crea ordenes de compra automaticas via `POST /ordenes-compra/`
4. **Notificacion**: Envia email al proveedor (si tiene email configurado)

### Configuracion

```bash
# Ejecutar script de configuracion automatica
cd n8n
python setup_n8n_workflow.py
# Sigue las instrucciones: ingresa la API Key de n8n cuando se solicite
```

### Endpoints usados por n8n

- `GET http://host.docker.internal:8000/insumos/alertas/` — Insumos bajo stock
- `POST http://host.docker.internal:8000/ordenes-compra/` — Crear orden
- `GET http://host.docker.internal:8000/proveedores/` — Obtener datos del proveedor

---

## Chatbot con Ollama

### Componentes

| Archivo | Descripcion |
|---------|-------------|
| `backend/chatbot/engine.py` | Motor del chatbot (Ollama + llama3.2) |
| `backend/chatbot/router.py` | Rutas de API para el chatbot |
| `backend/chatbot/knowledge_base.py` | Base de conocimiento del sistema |
| `backend/chatbot/data_fetcher.py` | Recuperacion de datos en tiempo real |

### Funcionamiento

- Utiliza el modelo `llama3.2` corriendo localmente via Ollama
- El chatbot tiene conocimiento del esquema completo de la base de datos
- Puede responder preguntas sobre ventas, produccion, predicciones, etc.
- Soporta entrada de texto y audio
- Frontend widget integrado en `frontend3/src/components/ChatbotWidget.jsx`

### Endpoints

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/chatbot/pregunta` | Enviar pregunta en texto |
| POST | `/chatbot/audio` | Enviar archivo de audio |

---

## Estructura del Proyecto

```
panaderia-v2/
├── backend/
│   ├── main.py                    # API FastAPI completa (~3800 lineas)
│   ├── models.py                  # Modelos SQLAlchemy (14 tablas)
│   ├── database.py                # Conexion a PostgreSQL
│   ├── Dockerfile                 # Contenedor del backend
│   ├── requirements.txt           # Dependencias Python (27 paquetes)
│   ├── ml/
│   │   ├── features.py            # Ingenieria de caracteristicas (13 variables)
│   │   ├── trainer.py             # Entrenamiento de modelos
│   │   ├── predictor.py           # Generacion de predicciones
│   │   ├── comparador.py          # Comparacion de 7 algoritmos
│   │   ├── seed_data.py           # Datos sinteticos iniciales
│   │   ├── weather_api.py         # Integracion Open-Meteo
│   │   ├── anomaly.py             # Deteccion de anomalias
│   │   ├── models/
│   │   │   └── registry.py        # Registro de todos los modelos (7 algoritmos)
│   │   └── models_trained/        # Modelos .pkl entrenados (218 archivos)
│   ├── chatbot/
│   │   ├── engine.py              # Motor del chatbot (Ollama)
│   │   ├── router.py              # Rutas del chatbot
│   │   ├── knowledge_base.py      # Base de conocimiento
│   │   └── data_fetcher.py        # Recuperacion de datos en vivo
│   ├── utils/
│   │   ├── helpers.py             # Roles fijos y funciones auxiliares
│   │   ├── email_utils.py         # Envio de emails (Gmail SMTP)
│   │   ├── notificaciones.py      # Notificaciones (email + Telegram)
│   │   ├── crypto.py              # Cifrado Fernet
│   │   ├── pdf_orden.py           # Generacion de PDF de ordenes
│   │   └── pdf_reporte.py         # Generacion de PDF de reportes
│   └── tests/
│       ├── conftest.py            # Configuracion de tests
│       └── test_routes.py         # Tests de rutas API
├── frontend3/
│   ├── package.json               # Dependencias Node (React 19 + Vite 8)
│   ├── vite.config.js             # Configuracion Vite + proxy
│   ├── Dockerfile                 # Contenedor multi-etapa (node + nginx)
│   ├── nginx.conf                 # Configuracion nginx para produccion
│   └── src/
│       ├── App.jsx                # Componente raiz + routing
│       ├── main.jsx              # Punto de entrada
│       ├── api/
│       │   └── api.js            # Cliente HTTP para backend
│       ├── components/
│       │   ├── Layout.jsx        # Layout principal
│       │   ├── Sidebar.jsx       # Barra lateral de navegacion
│       │   ├── Pagination.jsx    # Componente de paginacion
│       │   └── ChatbotWidget.jsx # Widget flotante del chatbot
│       ├── context/
│       │   ├── AuthContext.jsx   # Contexto de autenticacion
│       │   └── NavContext.jsx    # Contexto de navegacion
│       └── pages/                # 18 paginas del dashboard
├── n8n/
│   ├── n8n-workflow.json         # Workflow de automatizacion
│   └── setup_n8n_workflow.py     # Script de importacion del workflow
├── docker-compose.yml            # Orquestacion: DB, pgAdmin, n8n, backend, frontend
├── .env                          # Variables de entorno (ACTIVO - contiene credenciales)
├── .env.example                  # Template de variables de entorno
├── .gitignore                    # Archivos ignorados por git
└── README.md                     # Este archivo
```

---

## Testing

### Backend (pytest)

```bash
cd backend
pytest tests/ -v              # Todos los tests
pytest tests/ -v --cov=.      # Tests con cobertura
pytest tests/test_routes.py   # Tests especificos
```

### Frontend (ESLint)

```bash
cd frontend3
npm run lint
```

### Pruebas de integracion manual

```bash
# 1. Verificar estado del sistema
curl http://localhost:8000/sistema/estado

# 2. Verificar salud del sistema
curl http://localhost:8000/sistema/health

# 3. Verificar que el dashboard carga
# Abrir http://localhost:80 en el navegador

# 4. Probar login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "administrador"}'
```

---

## Referencias para Articulo Cientifico

### Justificacion de la seleccion tecnologica

**FastAPI** fue seleccionado como framework backend por su rendimiento (asincrono, basado en Starlette), tipado automatico con Pydantic, documentacion interactiva automatica (Swagger/OpenAPI) y facil integracion con librerias de ML. Comparado con Flask o Django REST, FastAPI ofrece 2-3x mejor rendimiento en benchmarks.

**scikit-learn** fue elegido para ML por su madurez, documentacion extensa, API consistente y compatibilidad con el ecosistema Python cientifico. Proporciona los 7 algoritmos necesarios sin dependencias adicionales pesadas.

**PostgreSQL** como base de datos relacional por su soporte de indices compuestos, integridad referencial, y rendimiento en consultas analiticas.

**React 19 + Vite 8** para el frontend por su rendimiento en desarrollo (HMR rapido), empaquetado optimizado, y ecosistema de componentes.

### Algoritmos de Machine Learning: fundamentos

1. **Random Forest** — Ensemble de 200 arboles de decision con bagging. Cada arbol se entrena con una muestra bootstrap y considera solo √n features por split. Promedia las predicciones de todos los arboles para reducir varianza. Ideal para datos tabulares con relaciones no lineales.

2. **Linear Regression** — Modelo parametrico que asume relacion lineal entre features y demanda. Coeficientes estimados por Minimos Cuadrados Ordinarios (OLS). Sirve como linea base interpretable.

3. **Gradient Boosting** — Construye arboles secuencialmente, donde cada uno corrige los errores del anterior. Learning rate=0.08 controla la contribucion de cada arbol. Generalmente supera a Random Forest en accuracy.

4. **ARIMA** — Modelo estadistico univariado (AutoRegressive Integrated Moving Average). Usa solo la historia de la serie temporal. Orden (1,0,1): un termino autorregresivo y uno de media movil, sin diferenciacion.

5. **Prophet** — Descomposicion de series temporales desarrollada por Meta. Separa la serie en tendencia (con changepoints), estacionalidad semanal (series de Fourier), y efectos de feriados. Modo multiplicativo.

6. **MLP Neural Network** — Perceptron Multicapa con 2 capas ocultas (64 y 32 neuronas), activacion ReLU, optimizador Adam, early stopping. Teorema de aproximacion universal: puede modelar cualquier funcion continua.

7. **Ensemble (RF+GB+LR)** — VotingRegressor con pesos 2:2:1. Combina diversidad de modelos (bagging + boosting + lineal) para reducir varianza y mejorar robustez.

### Metricas de evaluacion

- **MAE** (Mean Absolute Error): `Σ|y_real - y_pred| / n`. Error promedio absoluto en unidades de producto.
- **RMSE** (Root Mean Squared Error): `√(Σ(y_real - y_pred)² / n)`. Penaliza mas los errores grandes.
- **R²** (Coeficiente de determinacion): `1 - (Σ(y_real - y_pred)² / Σ(y_real - y_media)²)`. Proporcion de varianza explicada (0-1).

### Proceso de seleccion de modelo

Por cada producto (24 total):
1. Se cargan 60+ dias de datos historicos + climaticos
2. Se construyen 13 features por dia
3. Se particiona: train (ultimos 60+ dias), test (ultimos 30 dias)
4. Se entrenan los 7 algoritmos
5. Se evaluan en test set con MAE, RMSE, R²
6. Se selecciona el de menor RMSE como modelo final
7. Se guarda en `best_{producto_id}.pkl` y se registra en `best_model.json`

### Contribucion cientifica

Este sistema integra prediccion de demanda con automatizacion de cadena de suministro para el sector panadero artesanal, un area poco estudiada en la literatura. La combinacion de 7 algoritmos con seleccion automatica por producto permite adaptarse a diferentes patrones de demanda (panes de alta rotacion vs productos estacionales). La inclusion de datos climaticos locales (Pacasmayo) y calendario de feriados peruanos añade contexto geografico especifico.

---

## Notas de seguridad

1. Las credenciales de Gmail SMTP estan expuestas en `.env`. Se recomienda **rotar inmediatamente** la contrasena de aplicacion de Google y migrar a un gestor de secretos.
2. La autenticacion usa tokens en memoria (diccionario Python), no JWT. Esto significa que al reiniciar el backend, todas las sesiones se pierden.
3. CORS configurado con `allow_origins=["*"]` (sin restricciones). En produccion, restringir a origenes especificos.
4. Las contrasenas de los vendedores se almacenan en texto plano en `dim_vendedores.password`. Se recomienda implementar hashing.
5. No hay HTTPS configurado. Todo el trafico viaja en texto plano.

---

## Historial de versiones

- **v2.0** (Abril 2026) — Sistema completo con React 19, 7 algoritmos ML, n8n, 2FA, chatbot
- **v1.0** (2025) — Prototipo inicial con API basica y Streamlit

---

*Sistema desarrollado para la Tesis de Ingenieria — Universidad Nacional de Trujillo (UNT), Escuela de Ingenieria, 2026-I*
*Pacasmayo, La Libertad — Peru*
