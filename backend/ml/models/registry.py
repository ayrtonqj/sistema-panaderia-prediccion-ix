"""
registry.py — Catálogo de todos los modelos predictivos disponibles.
Cada modelo implementa la interfaz: train(X, y), predict(X), get_name(), get_metrics()
"""

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ALGORITHM_NAMES = [
    "Random Forest",
    "Linear Regression",
    "Gradient Boosting",
    "ARIMA",
    "Prophet",
    "MLP Neural Network",
    "Ensemble (RF+GB+LR)",
]

MODEL_REGISTRY = {}

# ── 1. Random Forest ──────────────────────────────────────────────────────────

try:
    from sklearn.ensemble import RandomForestRegressor

    class RandomForestModel:
        def __init__(self):
            self.model = None
            self.metrics = {}

        def get_name(self):
            return "Random Forest"

        def train(self, X, y):
            self.model = RandomForestRegressor(
                n_estimators=200, max_depth=8, min_samples_split=5,
                min_samples_leaf=3, max_features="sqrt", random_state=42, n_jobs=-1,
            )
            self.model.fit(X, y)
            return self

        def predict(self, X):
            return np.maximum(self.model.predict(X), 0)

        def evaluate(self, X_test, y_test):
            y_pred = self.predict(X_test)
            self.metrics = {
                "mae": round(mean_absolute_error(y_test, y_pred), 2),
                "rmse": round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
                "r2": round(r2_score(y_test, y_pred), 4),
            }
            return self.metrics

        def get_metrics(self):
            return self.metrics

        def get_feature_importance(self, feature_names=None):
            if hasattr(self.model, 'feature_importances_'):
                imp = self.model.feature_importances_
                if feature_names:
                    return dict(sorted(zip(feature_names, imp), key=lambda x: x[1], reverse=True))
                return imp.tolist()
            return []

        def get_detalles(self, feature_names=None):
            params = {
                "n_estimators (arboles)": getattr(self.model, "n_estimators", 200),
                "max_depth (profundidad maxima)": getattr(self.model, "max_depth", 8),
                "min_samples_split": getattr(self.model, "min_samples_split", 5),
                "min_samples_leaf": getattr(self.model, "min_samples_leaf", 3),
                "max_features": "sqrt(13) ≈ 4",
            }
            imp = self.get_feature_importance(feature_names)
            top_imp = []
            if isinstance(imp, dict) and feature_names:
                top_imp = [{"feature": k, "importance": round(float(v), 4)} for k, v in list(imp.items())[:6]]
            elif isinstance(imp, list) and len(imp) > 0:
                nombres = feature_names if feature_names else [f"x{i}" for i in range(len(imp))]
                top_imp = [{"feature": n, "importance": round(float(v), 4)} for n, v in list(zip(nombres, imp))[:6]]
            return {
                "formula": "Ensemble de 200 arboles de decision entrenados con bootstrap (bagging). Cada arbol aprende reglas del tipo 'SI temperatura > 25 Y lag_1 > 50 ENTONCES demanda ≈ X'. La prediccion final es el promedio de los 200 arboles, lo que reduce la varianza y el sobreajuste.",
                "como_funciona": [
                    "1. Bootstrap: Se generan 200 muestras aleatorias con reemplazo del conjunto de entrenamiento.",
                    "2. Arbol de decision: Cada muestra entrena un arbol que divide los datos segun la feature que mejor reduce el error cuadratico medio (MSE).",
                    "3. Aleatoriedad: En cada split solo se considera una muestra aleatoria de √13 ≈ 4 features, forzando diversidad entre arboles.",
                    "4. Ensamble (promedio): La prediccion final = promedio(arbol₁(X), arbol₂(X), ..., arbol₂₀₀(X)). Esto suaviza errores individuales.",
                ],
                "por_que_parametros": "n_estimators=200: suficiente para convergencia sin ser muy lento. max_depth=8: evita sobreajuste en datasets pequeños (<500 registros). min_samples_leaf=3: previene hojas con pocas muestras. max_features=sqrt: balance sesgo-varianza optimo.",
                "fortalezas": [
                    "Captura relaciones no lineales complejas sin necesidad de transformar features.",
                    "Robusto a outliers y datos ruidosos porque promedia multiples arboles.",
                    "No requiere escalado/normalizacion de features.",
                    "Provee importancia de features (cuales variables pesan mas).",
                ],
                "debilidades": [
                    "Menos interpretable que regresion lineal (no hay una ecuacion simple).",
                    "Puede ser lento en prediccion con muchos arboles (aunque 200 es manejable).",
                    "Tiende a suavizar valores extremos (dificil predecir picos de demanda).",
                ],
                "complejidad": "media",
                "velocidad": "rapida",
                "interpretabilidad": "media",
                "parametros": params,
                "feature_importance": top_imp,
            }

    MODEL_REGISTRY["Random Forest"] = RandomForestModel
except Exception as e:
    print(f"[MODEL] Random Forest no disponible: {e}")


# ── 2. Linear Regression ─────────────────────────────────────────────────────

try:
    from sklearn.linear_model import LinearRegression

    class LinearRegressionModel:
        def __init__(self):
            self.model = None
            self.metrics = {}

        def get_name(self):
            return "Linear Regression"

        def train(self, X, y):
            self.model = LinearRegression()
            self.model.fit(X, y)
            return self

        def predict(self, X):
            return np.maximum(self.model.predict(X), 0)

        def evaluate(self, X_test, y_test):
            y_pred = self.predict(X_test)
            self.metrics = {
                "mae": round(mean_absolute_error(y_test, y_pred), 2),
                "rmse": round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
                "r2": round(r2_score(y_test, y_pred), 4),
            }
            return self.metrics

        def get_metrics(self):
            return self.metrics

        def get_detalles(self, feature_names=None):
            coefs = []
            intercept = 0
            if hasattr(self.model, "coef_"):
                nombres = feature_names if feature_names else [f"x{i}" for i in range(len(self.model.coef_))]
                pares = sorted(zip(nombres, self.model.coef_), key=lambda x: abs(x[1]), reverse=True)
                coefs = [{"feature": n, "coef": round(float(c), 4)} for n, c in pares[:8]]
                intercept = round(float(self.model.intercept_), 4)
            formula_str = f"Demanda = {intercept:.1f}"
            for c in coefs[:5]:
                signo = "+" if c["coef"] >= 0 else ""
                formula_str += f" {signo}{c['coef']:.1f}·{c['feature']}"
            formula_str += " + ..."
            return {
                "formula": f"Regresion Lineal Multiple por Minimos Cuadrados Ordinarios (OLS). Ecuacion: {formula_str}. El modelo asume que la demanda es una combinacion lineal de las 13 features. Cada coeficiente βᵢ indica cuanto cambia la demanda al aumentar en 1 unidad la feature xᵢ, manteniendo las demas constantes.",
                "como_funciona": [
                    "1. Ecuacion: Demanda = β₀ + β₁·lag₁ + β₂·lag₇ + ... + β₁₃·rolling₃₀ + ε",
                    "2. Entrenamiento (OLS): Se eligen los β que minimizan la suma de errores al cuadrado: min Σ(y_real - y_pred)²",
                    "3. Solucion: Los coeficientes β se calculan con la formula matricial β = (XᵀX)⁻¹Xᵀy.",
                    "4. Prediccion: Para nuevas features X_nuevo, la demanda = β₀ + X_nuevo · β.",
                ],
                "por_que_parametros": "Sin hiperparametros (modelo parametrico). La simplicidad es su ventaja: entrena instantaneamente y los coeficientes son directamente interpretables.",
                "fortalezas": [
                    "Maxima interpretabilidad: cada coeficiente tiene un significado claro (ej: +2.5 en lag_1 significa que la demanda de ayer pesa +2.5 unidades).",
                    "Entrenamiento casi instantaneo (solucion analitica cerrada).",
                    "Excelente linea base: si LR funciona bien, el problema es aproximadamente lineal.",
                    "No requiere ajuste de hiperparametros.",
                ],
                "debilidades": [
                    "Solo captura relaciones lineales. No detecta patrones como 'fines de semana disparan la demanda' a menos que esten codificados en features.",
                    "Muy sensible a outliers (un dato extremo tuerce todos los coeficientes).",
                    "Asume independencia de errores (no apto para series temporales con autocorrelacion fuerte).",
                    "Multicolinealidad entre features puede inflar la varianza de los coeficientes.",
                ],
                "complejidad": "baja",
                "velocidad": "muy rapida",
                "interpretabilidad": "muy alta",
                "parametros": {"intercept (β₀)": intercept},
                "coeficientes": coefs,
                "feature_importance": [],
            }

    MODEL_REGISTRY["Linear Regression"] = LinearRegressionModel
except Exception as e:
    print(f"[MODEL] Linear Regression no disponible: {e}")


# ── 3. Gradient Boosting ─────────────────────────────────────────────────────

try:
    from sklearn.ensemble import GradientBoostingRegressor

    class GradientBoostingModel:
        def __init__(self):
            self.model = None
            self.metrics = {}

        def get_name(self):
            return "Gradient Boosting"

        def train(self, X, y):
            self.model = GradientBoostingRegressor(
                n_estimators=150, max_depth=5, min_samples_leaf=3,
                learning_rate=0.08, random_state=42,
            )
            self.model.fit(X, y)
            return self

        def predict(self, X):
            return np.maximum(self.model.predict(X), 0)

        def evaluate(self, X_test, y_test):
            y_pred = self.predict(X_test)
            self.metrics = {
                "mae": round(mean_absolute_error(y_test, y_pred), 2),
                "rmse": round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
                "r2": round(r2_score(y_test, y_pred), 4),
            }
            return self.metrics

        def get_metrics(self):
            return self.metrics

        def get_detalles(self, feature_names=None):
            params = {
                "n_estimators (arboles secuenciales)": getattr(self.model, "n_estimators", 150),
                "max_depth": getattr(self.model, "max_depth", 5),
                "learning_rate (tasa de aprendizaje)": getattr(self.model, "learning_rate", 0.08),
                "loss": "squared_error (MSE)",
            }
            imp = []
            if hasattr(self.model, "feature_importances_"):
                nombres = feature_names if feature_names else [f"x{i}" for i in range(len(self.model.feature_importances_))]
                pares = sorted(zip(nombres, self.model.feature_importances_), key=lambda x: x[1], reverse=True)
                imp = [{"feature": n, "importance": round(float(v), 4)} for n, v in pares[:6]]
            return {
                "formula": "Gradient Boosting construye arboles de decision en secuencia. El primer arbol predice la demanda base. Cada arbol siguiente se entrena para predecir el ERROR residual del arbol anterior (los 'errores que quedan por corregir'). La prediccion final es la suma ponderada: F(x) = Σ learning_rate × arbolᵢ(x).",
                "como_funciona": [
                    "1. Inicializacion: Se parte de una prediccion constante F₀ = media(y).",
                    "2. Iteracion (150 veces): Se calcula el error residual rᵢ = y - F(x). Se entrena un arbol pequeño (max_depth=5) para predecir rᵢ.",
                    "3. Actualizacion: F(x) += learning_rate × arbol(x). El learning_rate=0.08 evita sobreajuste.",
                    "4. Resultado: Despues de 150 iteraciones, F(x) es una suma de 150 arboles que corrige errores progresivamente.",
                ],
                "por_que_parametros": "n_estimators=150: arboles suficientes para converger. max_depth=5: arboles poco profundos (weak learners) que evitan memorizar ruido. learning_rate=0.08: paso pequeño para convergencia suave.",
                "fortalezas": [
                    "Generalmente supera a Random Forest en accuracy porque corrige errores secuencialmente.",
                    "Maneja bien datos con ruido moderado.",
                    "No requiere escalado de features.",
                    "Provee importancia de features.",
                ],
                "debilidades": [
                    "Mas propenso a sobreajuste que Random Forest si hay mucho ruido.",
                    "Entrenamiento secuencial (no paralelizable), mas lento que RF.",
                    "Sensible a hiperparametros: learning_rate y n_estimators deben balancearse.",
                    "Tiende a enfocarse en outliers si no se controla.",
                ],
                "complejidad": "media",
                "velocidad": "media",
                "interpretabilidad": "media",
                "parametros": params,
                "feature_importance": imp,
            }

    MODEL_REGISTRY["Gradient Boosting"] = GradientBoostingModel
except Exception as e:
    print(f"[MODEL] Gradient Boosting no disponible: {e}")


# ── 4. ARIMA ──────────────────────────────────────────────────────────────────

try:
    from statsmodels.tsa.arima.model import ARIMA

    class ARIMAModel:
        def __init__(self):
            self.model = None
            self.results = None
            self.metrics = {}
            self.last_train_y = None
            self.order_usado = None

        def get_name(self):
            return "ARIMA"

        def train(self, X, y):
            self.last_train_y = y
            for order in [(1, 0, 1), (1, 0, 0)]:
                try:
                    self.model = ARIMA(y, order=order)
                    self.results = self.model.fit()
                    self.order_usado = order
                    break
                except Exception:
                    self.results = None
            self.model = self.results
            return self

        def predict(self, X):
            n = X.shape[0]
            if self.results is None:
                return np.full(n, np.mean(self.last_train_y) if self.last_train_y is not None else 0)
            try:
                forecast = self.results.forecast(steps=n)
                return np.maximum(forecast.values if hasattr(forecast, 'values') else forecast, 0)
            except Exception:
                return np.full(n, np.mean(self.last_train_y) if self.last_train_y is not None else 0)

        def evaluate(self, X_test, y_test):
            y_pred = self.predict(X_test)
            self.metrics = {
                "mae": round(mean_absolute_error(y_test, y_pred), 2),
                "rmse": round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
                "r2": round(r2_score(y_test, y_pred), 4),
            }
            return self.metrics

        def get_metrics(self):
            return self.metrics

        def get_detalles(self, feature_names=None):
            order = self.order_usado or (1, 0, 1)
            aic = round(float(self.results.aic), 2) if self.results and hasattr(self.results, "aic") else None
            bic = round(float(self.results.bic), 2) if self.results and hasattr(self.results, "bic") else None
            return {
                "formula": f"ARIMA(p={order[0]}, d={order[1]}, q={order[2]}) es un modelo estadistico univariado que predice la demanda usando exclusivamente la historia de la serie temporal. NO usa features externas (clima, feriados, etc.). Ecuacion: yₜ = c + φ₁yₜ₋₁ + ... + φₚyₜ₋ₚ + θ₁εₜ₋₁ + ... + θ_qεₜ₋_q + εₜ.",
                "como_funciona": [
                    "1. AR (AutoRegresivo, p): La demanda de hoy depende de la demanda de dias anteriores. Con p=1, yₜ = c + φ₁·yₜ₋₁ + εₜ.",
                    "2. I (Integrado, d): Se aplican diferencias para hacer la serie estacionaria. Con d=0, no se diferencian los datos.",
                    "3. MA (Media Movil, q): El modelo incluye los errores de prediccion pasados. Con q=1, se corrige con el error de ayer εₜ₋₁.",
                    "4. Ajuste por Maxima Verosimilitud (MLE): Se eligen los parametros φ, θ que maximizan la probabilidad de observar los datos historicos.",
                ],
                "por_que_parametros": "ARIMA(1,0,1) es un modelo simple y robusto para series diarias. d=0 porque las ventas diarias no suelen tener tendencia fuerte en periodos cortos. Fallback (1,0,0) si (1,0,1) no converge. AIC/BIC miden calidad de ajuste penalizando complejidad (menor = mejor).",
                "fortalezas": [
                    "Modelo estadistico clasico con fundamento matematico solido.",
                    "AIC/BIC permiten comparar objetivamente diferentes ordenes (p,d,q).",
                    "No requiere features externas: funciona solo con la historia de ventas.",
                    "Captura patrones temporales como inercia (ayer influye en hoy).",
                ],
                "debilidades": [
                    "No utiliza features externas (clima, feriados) que pueden ser muy predictivas.",
                    "Asume que la serie es estacionaria (media y varianza constantes).",
                    "Poco efectivo con pocos datos (<50 puntos).",
                    "No captura estacionalidad semanal sin SARIMA (que es mas complejo).",
                ],
                "complejidad": "baja",
                "velocidad": "rapida",
                "interpretabilidad": "alta",
                "parametros": {"order (p,d,q)": list(order), "AIC": aic, "BIC": bic},
                "feature_importance": [],
            }

    MODEL_REGISTRY["ARIMA"] = ARIMAModel
except Exception as e:
    print(f"[MODEL] ARIMA no disponible: {e}")


# ── 5. Prophet ────────────────────────────────────────────────────────────────

try:
    from prophet import Prophet
    import pandas as pd

    class ProphetModel:
        def __init__(self):
            self.model = None
            self.metrics = {}
            self.last_y = None

        def get_name(self):
            return "Prophet"

        def train(self, X, y):
            self.last_y = y
            df = pd.DataFrame({
                "ds": pd.date_range(end="today", periods=len(y), freq="D"),
                "y": y,
            })
            self.model = Prophet(
                yearly_seasonality=False,
                weekly_seasonality=True,
                daily_seasonality=False,
                seasonality_mode="multiplicative",
                changepoint_prior_scale=0.05,
                interval_width=0.8,
            )
            self.model.add_seasonality(name="weekly", period=7, fourier_order=3)
            self.model.fit(df, verbose=False)
            return self

        def predict(self, X):
            n = X.shape[0]
            future = pd.DataFrame({
                "ds": pd.date_range(start="today", periods=n, freq="D"),
            })
            forecast = self.model.predict(future)
            return np.maximum(forecast["yhat"].values, 0)

        def evaluate(self, X_test, y_test):
            y_pred = self.predict(X_test)
            self.metrics = {
                "mae": round(mean_absolute_error(y_test, y_pred), 2),
                "rmse": round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
                "r2": round(r2_score(y_test, y_pred), 4),
            }
            return self.metrics

        def get_metrics(self):
            return self.metrics

        def get_detalles(self, feature_names=None):
            return {
                "formula": "Prophet (Meta, 2017) descompone la serie temporal en 3 componentes aditivos: y(t) = g(t) + s(t) + h(t) + ε. g(t)=tendencia (logistica o lineal con changepoints), s(t)=estacionalidad semanal modelada con series de Fourier (3 terminos = captura patrones suaves), h(t)=efecto de feriados y eventos especiales, ε=ruido normal.",
                "como_funciona": [
                    "1. Tendencia g(t): Modelo lineal por tramos con puntos de cambio (changepoints) detectados automaticamente. El parametro changepoint_prior_scale=0.05 controla la flexibilidad.",
                    "2. Estacionalidad s(t): Ajusta una curva suave semanal usando 3 terminos de Fourier: sin(2πt/7), cos(2πt/7), sin(4πt/7), etc. Modo multiplicativo: el efecto semanal escala con el nivel.",
                    "3. Feriados h(t): Cada feriado tiene un impacto estimado (positivo o negativo) sobre la demanda.",
                    "4. Inferencia Bayesiana: Ajusta todos los parametros simultaneamente usando Stan (MCMC).",
                ],
                "por_que_parametros": "weekly_seasonality=True: captura patron dia-de-semana. seasonality_mode='multiplicative': el efecto semanal es proporcional al volumen (ej: sabado +30% sobre la media). changepoint_prior_scale=0.05: balance entre ajuste y suavidad de tendencia. Fourier order 3: suficiente para patron semanal suave sin sobreajuste.",
                "fortalezas": [
                    "Descomposicion interpretable: puedes ver tendencia, estacionalidad y feriados por separado.",
                    "Maneja automaticamente datos faltantes y outliers.",
                    "Disenado especificamente para forecasting de negocio (Meta lo usa internamente).",
                    "Incluye intervalos de confianza (yhat_lower, yhat_upper).",
                ],
                "debilidades": [
                    "Lento comparado con otros metodos (inferencia bayesiana).",
                    "Puede fallar con pocos datos (<60 puntos).",
                    "Requiere la libreria cmdstanpy (dependencia pesada).",
                    "No usa features externas adicionales fuera de feriados (ignora clima, eventos, etc.).",
                ],
                "complejidad": "alta",
                "velocidad": "lenta",
                "interpretabilidad": "alta",
                "parametros": {
                    "seasonality_mode": "multiplicative",
                    "weekly_seasonality": True,
                    "changepoint_prior_scale": 0.05,
                    "fourier_order": 3,
                },
                "feature_importance": [],
            }

    MODEL_REGISTRY["Prophet"] = ProphetModel
except Exception as e:
    print(f"[MODEL] Prophet no disponible: {e}")


# ── 6. MLP Neural Network ────────────────────────────────────────────────────

try:
    from sklearn.neural_network import MLPRegressor

    class MLPModel:
        def __init__(self):
            self.model = None
            self.metrics = {}

        def get_name(self):
            return "MLP Neural Network"

        def train(self, X, y):
            self.model = MLPRegressor(
                hidden_layer_sizes=(64, 32), activation='relu',
                solver='adam', max_iter=500, random_state=42,
                early_stopping=True, validation_fraction=0.1,
            )
            self.model.fit(X, y)
            return self

        def predict(self, X):
            return np.maximum(self.model.predict(X), 0)

        def evaluate(self, X_test, y_test):
            y_pred = self.predict(X_test)
            self.metrics = {
                "mae": round(mean_absolute_error(y_test, y_pred), 2),
                "rmse": round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
                "r2": round(r2_score(y_test, y_pred), 4),
            }
            return self.metrics

        def get_metrics(self):
            return self.metrics

        def get_detalles(self, feature_names=None):
            params = {
                "hidden_layers": list(getattr(self.model, "hidden_layer_sizes", (64, 32))),
                "activation": getattr(self.model, "activation", "relu"),
                "solver (optimizador)": getattr(self.model, "solver", "adam"),
                "max_iter (maximo)": getattr(self.model, "max_iter", 500),
                "n_iter (iteraciones reales)": int(getattr(self.model, "n_iter_", 0)),
                "n_layers (capas totales)": int(getattr(self.model, "n_layers_", 3)),
            }
            return {
                "formula": "Red Neuronal Perceptron Multicapa (MLP) con arquitectura: Entrada(13 features) → Capa Oculta₁(64 neuronas, ReLU) → Capa Oculta₂(32 neuronas, ReLU) → Salida(1 neurona, sin activacion = regresion). Cada neurona aplica: salida = ReLU(Σ wᵢ·xᵢ + b). Optimizador Adam ajusta los pesos w y sesgos b para minimizar el MSE.",
                "como_funciona": [
                    "1. Forward Pass: Los 13 valores de features fluyen desde la entrada, pasando por 64 y luego 32 neuronas. Cada neurona calcula una suma ponderada y aplica ReLU (max(0, x)) para introducir no-linealidad.",
                    "2. Calculo del error: Se compara la prediccion con la demanda real usando MSE = (y_pred - y_real)².",
                    "3. Backpropagation: El error se propaga hacia atras. Adam (Adaptive Moment Estimation) ajusta cada peso w en la direccion que reduce el error, con learning rate adaptativo por parametro.",
                    "4. Early Stopping: Si el error en el 10% de validacion no mejora por varias iteraciones, el entrenamiento se detiene para evitar sobreajuste.",
                ],
                "por_que_parametros": "hidden_layers=(64,32): arquitectura tipo embudo que comprime la informacion progresivamente. ReLU: activacion estandar que evita el problema de gradientes evanescentes. Adam: optimizador moderno con momentun y learning rate adaptativo. max_iter=500: pocas iteraciones porque hay pocos datos. Early stopping: evita sobreajuste automaticamente.",
                "fortalezas": [
                    "Puede modelar relaciones extremadamente complejas y no lineales.",
                    "Aprendizaje automatico de interacciones entre features (no requiere ingenieria manual).",
                    "Early stopping integrado previene sobreajuste.",
                    "Teoricamente puede aproximar cualquier funcion continua (teorema de aproximacion universal).",
                ],
                "debilidades": [
                    "Caja negra: muy dificil interpretar por que predice X.",
                    "Requiere mas datos que metodos lineales para generalizar bien.",
                    "Sensible a la escala de los features (requiere normalizacion).",
                    "Los pesos iniciales son aleatorios (resultados pueden variar entre ejecuciones).",
                ],
                "complejidad": "alta",
                "velocidad": "media",
                "interpretabilidad": "baja",
                "parametros": params,
                "feature_importance": [],
            }

    MODEL_REGISTRY["MLP Neural Network"] = MLPModel
except Exception as e:
    print(f"[MODEL] MLP Neural Network no disponible: {e}")


# ── 7. Ensemble (VotingRegressor con RF + GradientBoosting + LinearRegression) ─

try:
    from sklearn.ensemble import VotingRegressor

    class EnsembleModel:
        def __init__(self):
            self.model = None
            self.metrics = {}
            self.sub_models = {}

        def get_name(self):
            return "Ensemble (RF+GB+LR)"

        def train(self, X, y):
            from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
            from sklearn.linear_model import LinearRegression

            rf = RandomForestRegressor(
                n_estimators=100, max_depth=6, random_state=42, n_jobs=-1
            )
            gb = GradientBoostingRegressor(
                n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42
            )
            lr = LinearRegression()

            self.model = VotingRegressor(
                estimators=[("rf", rf), ("gb", gb), ("lr", lr)],
                weights=[2, 2, 1],
            )
            self.model.fit(X, y)
            return self

        def predict(self, X):
            return np.maximum(self.model.predict(X), 0)

        def evaluate(self, X_test, y_test):
            y_pred = self.predict(X_test)
            self.metrics = {
                "mae": round(mean_absolute_error(y_test, y_pred), 2),
                "rmse": round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
                "r2": round(r2_score(y_test, y_pred), 4),
            }
            return self.metrics

        def get_metrics(self):
            return self.metrics

        def get_detalles(self, feature_names=None):
            return {
                "formula": "VotingRegressor (Ensemble por Votacion Ponderada). Combina 3 modelos heterogeneos: Random Forest (peso 2), Gradient Boosting (peso 2), Linear Regression (peso 1). Prediccion final = (2·RF + 2·GB + 1·LR) / 5. Al combinar modelos de distinta naturaleza (arboles + boosting + lineal), el ensemble aprovecha las fortalezas de cada uno y compensa sus debilidades.",
                "como_funciona": [
                    "1. Entrenamiento independiente: Random Forest, Gradient Boosting y Linear Regression se entrenan por separado con los mismos datos.",
                    "2. Votacion ponderada: Cada modelo predice la demanda. El voto de RF y GB vale el doble que el de LR porque historicamente tienen mejor desempeño en este dominio.",
                    "3. Promedio: Prediccion = (2×pred_RF + 2×pred_GB + 1×pred_LR) / 5.",
                    "4. Diversidad: Al usar algoritmos fundamentalmente diferentes (bagging, boosting, lineal), el ensemble reduce la varianza total (riesgo de que un solo modelo falle).",
                ],
                "por_que_parametros": "Pesos 2:2:1 porque RF y GB suelen superar a LR en datos de ventas (relaciones no lineales). LR recibe peso menor pero aporta estabilidad y evita que el ensemble se desvie por sobreajuste de los arboles. n_estimators reducidos (100) para RF/GB dentro del ensemble porque la combinacion ya aporta robustez.",
                "fortalezas": [
                    "Combina lo mejor de 3 mundos: no lineal (RF), correccion de errores (GB), estabilidad (LR).",
                    "Mas robusto que cualquier modelo individual: si uno falla, los otros compensan.",
                    "Reduce el riesgo de elegir un mal modelo (principio de 'sabiduria de multitudes').",
                    "Tiende a dar predicciones mas estables y con menos varianza.",
                ],
                "debilidades": [
                    "Mas lento que un modelo unico (entrena 3 modelos).",
                    "Mayor consumo de memoria (almacena 3 modelos).",
                    "Si los 3 modelos comenten el mismo error sistematico, el ensemble no lo corrige.",
                    "Los pesos (2:2:1) son fijos y no se optimizan automaticamente.",
                ],
                "complejidad": "alta",
                "velocidad": "lenta",
                "interpretabilidad": "baja",
                "parametros": {"sub_modelos": ["Random Forest (peso 2)", "Gradient Boosting (peso 2)", "Linear Regression (peso 1)"], "formula_votacion": "(2×RF + 2×GB + 1×LR) / 5"},
                "feature_importance": [],
            }

    MODEL_REGISTRY["Ensemble (RF+GB+LR)"] = EnsembleModel
except Exception as e:
    print(f"[MODEL] Ensemble no disponible: {e}")


def get_all_models():
    """Retorna lista de (nombre, clase_modelo) para todos los modelos disponibles."""
    return list(MODEL_REGISTRY.items())
