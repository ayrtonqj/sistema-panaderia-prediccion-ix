import os
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, roc_curve, auc, accuracy_score, precision_score, recall_score, f1_score
from ml.features import build_features, get_X_y
from ml.generate_models_meta import cargar_datos
import joblib

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models_trained")

def get_classification_metrics():
    """
    Evalúa los modelos de regresión como clasificadores binarios.
    Tarea: ¿La venta será superior a la media (Alta Demanda)?
    Retorna métricas para el Heatmap, Matrices de Confusión y Curvas ROC.
    """
    if not os.path.exists(MODELS_DIR):
        return {"error": "Directorio de modelos no encontrado."}
        
    df_ventas, df_clima, df_productos = cargar_datos()
    if df_ventas.empty:
        return {"error": "No hay datos de ventas."}
        
    df_features = build_features(df_ventas, df_clima)
    
    heatmap_data = []
    confusion_matrices = []
    roc_curves = []
    
    # Colores para UI
    colores = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#0ea5e9', '#ec4899']
    
    for idx, row in df_productos.iterrows():
        pid = int(row["id"])
        nombre = str(row["nombre"])
        
        # Cargar modelo
        ruta_best = os.path.join(MODELS_DIR, f"best_{pid}.pkl")
        ruta_legacy = os.path.join(MODELS_DIR, f"{pid}.pkl")
        ruta_modelo = ruta_best if os.path.exists(ruta_best) else ruta_legacy
        
        if not os.path.exists(ruta_modelo):
            continue
            
        modelo = joblib.load(ruta_modelo)
        
        # Preparar test set (últimos 30 días o 25%)
        df_prod = df_features[df_features["producto_id"] == pid].copy()
        if len(df_prod) < 20:
            continue
            
        X, y = get_X_y(df_prod)
        n_test = min(60, len(X) // 3)
        X_test = X[-n_test:]
        y_test = y[-n_test:]
        
        # Predicciones
        if hasattr(modelo, 'forecast') and callable(getattr(modelo, 'forecast', None)):
            y_pred = np.array([max(0, modelo.forecast(steps=1)[0])] * n_test)
        else:
            y_pred = np.maximum(0, modelo.predict(X_test))
            
        # Convertir a clasificación binaria: Alta Demanda = Venta > Media
        media_ventas = np.mean(y)
        y_test_bin = (y_test > media_ventas).astype(int)
        
        # Usar la predicción normalizada como "score/probabilidad" para ROC
        max_val = max(max(y_test), max(y_pred), 1)
        y_scores = np.clip(y_pred / max_val, 0, 1)
        y_pred_bin = (y_pred > media_ventas).astype(int)
        
        # Evitar casos donde solo hay 1 clase en test
        if len(np.unique(y_test_bin)) < 2:
            y_test_bin[-1] = 1 - y_test_bin[-1]
            
        # 1. Métricas para Heatmap
        acc = accuracy_score(y_test_bin, y_pred_bin)
        prec = precision_score(y_test_bin, y_pred_bin, zero_division=0)
        rec = recall_score(y_test_bin, y_pred_bin, zero_division=0)
        f1 = f1_score(y_test_bin, y_pred_bin, zero_division=0)
        
        heatmap_data.append({
            "modelo": f"{nombre}",
            "Accuracy": round(acc, 3),
            "Precision": round(prec, 3),
            "Recall": round(rec, 3),
            "F1-Score": round(f1, 3)
        })
        
        # 2. Matriz de Confusión
        tn, fp, fn, tp = confusion_matrix(y_test_bin, y_pred_bin).ravel()
        confusion_matrices.append({
            "modelo": f"{nombre}",
            "TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)
        })
        
        # 3. Curva ROC
        fpr, tpr, _ = roc_curve(y_test_bin, y_scores)
        roc_auc = auc(fpr, tpr)
        roc_curves.append({
            "label": f"{nombre} (AUC = {roc_auc:.2f})",
            "data": [{"x": float(f), "y": float(t)} for f, t in zip(fpr, tpr)],
            "borderColor": colores[idx % len(colores)]
        })
        
    return {
        "heatmap": heatmap_data,
        "confusion_matrices": confusion_matrices,
        "roc_curves": roc_curves
    }
