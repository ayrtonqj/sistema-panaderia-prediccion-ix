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
    "SARIMA",
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

    MODEL_REGISTRY["Gradient Boosting"] = GradientBoostingModel
except Exception as e:
    print(f"[MODEL] Gradient Boosting no disponible: {e}")


# ── 4. SARIMA (estacional) ───────────────────────────────────────────────────

try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    class SARIMAModel:
        def __init__(self):
            self.model = None
            self.results = None
            self.metrics = {}
            self.last_train_y = None

        def get_name(self):
            return "SARIMA"

        def train(self, X, y):
            self.last_train_y = y
            try:
                self.model = SARIMAX(
                    y, order=(1, 0, 1), seasonal_order=(1, 0, 1, 7),
                    enforce_stationarity=False, enforce_invertibility=False,
                )
                self.results = self.model.fit(disp=False, maxiter=100, method='innovations_mle')
            except Exception:
                try:
                    self.model = SARIMAX(
                        y, order=(1, 0, 0), seasonal_order=(0, 0, 1, 7),
                        enforce_stationarity=False, enforce_invertibility=False,
                    )
                    self.results = self.model.fit(disp=False, maxiter=100)
                except Exception:
                    self.results = None
            return self

        def predict(self, X):
            n = X.shape[0]
            if self.results is None:
                return np.full(n, np.mean(self.last_train_y) if self.last_train_y is not None else 0)
            try:
                forecast = self.results.forecast(steps=n)
                return np.maximum(forecast.values, 0)
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

    MODEL_REGISTRY["SARIMA"] = SARIMAModel
except Exception as e:
    print(f"[MODEL] SARIMA no disponible: {e}")


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

    MODEL_REGISTRY["Ensemble (RF+GB+LR)"] = EnsembleModel
except Exception as e:
    print(f"[MODEL] Ensemble no disponible: {e}")


def get_all_models():
    """Retorna lista de (nombre, clase_modelo) para todos los modelos disponibles."""
    return list(MODEL_REGISTRY.items())
