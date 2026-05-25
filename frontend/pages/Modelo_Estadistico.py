import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Modelo ML | Panaderia Victoria", page_icon="🤖", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.main{background:#0f1117;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#1a1f2e,#0d1117);border-right:1px solid #2d3748;}
</style>""", unsafe_allow_html=True)

API = "http://localhost:8000"

st.markdown("# 📈 Estadisticas del Modelo de Prediccion")
st.markdown("Metricas de evaluacion del modelo de inteligencia artificial. Un modelo entrenado para cada producto.")

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🔄 Reentrenar modelos", use_container_width=True):
        with st.spinner("Entrenando Random Forest para todos los productos... (puede tardar ~1 min)"):
            try:
                r = requests.post(f"{API}/ml/entrenar", timeout=120)
                if r.status_code == 200:
                    st.success("✅ Modelos reentrenados correctamente.")
                    st.rerun()
                else:
                    st.error(f"Error: {r.text}")
            except Exception as e:
                st.error(f"Timeout o error: {e}")

st.markdown("---")

try:
    metricas_raw = requests.get(f"{API}/ml/metricas", timeout=5).json()
    modelos = metricas_raw.get("modelos", [])
    df_ml = pd.DataFrame(modelos)
    df_disponibles = df_ml[df_ml["modelo_disponible"] == True].copy()

    if df_disponibles.empty:
        st.warning("No hay modelos entrenados. Usa el boton 'Reentrenar modelos'.")
        st.stop()

    r2_prom = df_disponibles["r2"].mean()
    mae_prom = df_disponibles["mae"].mean()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "📊 Modelos entrenados",
        len(df_disponibles),
        help="Cantidad de modelos que aprendieron a predecir. Uno por cada producto." )
    col2.metric(
        "📐 R² promedio",
        f"{r2_prom:.3f}",
        delta="Objetivo >0.5",
        help="Que tan bien explica el modelo las ventas. Rango 0-1. Mayor es mejor. Si supera 0.5, el modelo es util para planificar produccion." )
    col3.metric(
        "⚡ MAE promedio",
        f"{mae_prom:.2f} uds",
        help="En promedio, el modelo se equivoca por esta cantidad de unidades. Menor es mejor." )
    col4.metric(
        "🧠 Algoritmo",
        "Random Forest",
        help="Metodo de inteligencia artificial que combina muchos arboles de decision para hacer predicciones." )

    st.markdown("### 📐 Coeficiente R² por Producto")
    st.caption("Mide que tan bien el modelo explica las ventas de cada producto.")

    df_sort = df_disponibles.sort_values("r2", ascending=True)
    colores = ["#f87171" if r < 0.4 else "#fbbf24" if r < 0.6 else "#34d399" for r in df_sort["r2"]]

    fig_r2 = go.Figure(go.Bar(
        x=df_sort["r2"], y=df_sort["producto_nombre"],
        orientation="h", marker_color=colores,
        text=[f"R²={v:.4f}" for v in df_sort["r2"]], textposition="outside",
    ))
    fig_r2.add_vline(x=0.5, line_color="#f59e0b", line_dash="dash",
                     annotation_text="Umbral aceptable (0.5)", annotation_font_color="#f59e0b")
    fig_r2.update_layout(
        xaxis=dict(title="R²", range=[0, 1.1], gridcolor="#2d4a6a"),
        plot_bgcolor="#1e2a3a", paper_bgcolor="#1e2a3a",
        font=dict(color="#e2e8f0", family="Inter"), height=350,
    )
    st.plotly_chart(fig_r2, use_container_width=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("### ⚡ Error Absoluto Medio (MAE)")
        st.caption("Promedio de unidades que el modelo se equivoca.")
        fig_mae = px.bar(df_disponibles.sort_values("mae"), x="mae", y="producto_nombre",
                         orientation="h", color="mae", color_continuous_scale="Oranges",
                         text="mae")
        fig_mae.update_layout(plot_bgcolor="#1e2a3a", paper_bgcolor="#1e2a3a",
                              font=dict(color="#e2e8f0"), coloraxis_showscale=False,
                              xaxis_title="MAE (unidades)", yaxis_title="", height=300)
        st.plotly_chart(fig_mae, use_container_width=True)

    with col_r:
        st.markdown("### Error Cuadratico Medio (RMSE)")
        st.caption("RMSE: penaliza errores grandes.")
        fig_rmse = px.bar(df_disponibles.sort_values("rmse"), x="rmse", y="producto_nombre",
                          orientation="h", color="rmse", color_continuous_scale="Reds",
                          text="rmse")
        fig_rmse.update_layout(plot_bgcolor="#1e2a3a", paper_bgcolor="#1e2a3a",
                               font=dict(color="#e2e8f0"), coloraxis_showscale=False,
                               xaxis_title="RMSE (unidades)", yaxis_title="", height=300)
        st.plotly_chart(fig_rmse, use_container_width=True)

    st.markdown("### 📋 Tabla de metricas completa")
    df_tabla = df_disponibles[["producto_nombre", "r2", "mae", "rmse"]].copy()
    df_tabla.columns = ["Producto", "R²", "MAE (uds)", "RMSE (uds)"]
    df_tabla["Interpretacion"] = df_tabla["R²"].apply(
        lambda r: "✅ Bueno" if r >= 0.5 else "⚠️ Mejorable"
    )
    st.dataframe(df_tabla, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 📉 Comparacion Prediccion vs. Ventas Reales")
    st.caption("Compara que tan cerca estuvo la prediccion de la IA de las ventas reales.")

    dias_eval = st.slider("Dias a evaluar:", 7, 60, 30)
    try:
        comp_raw = requests.get(f"{API}/predicciones/vs-real?dias={dias_eval}", timeout=5).json()
        comparaciones = comp_raw.get("comparaciones", 0)
        mae_global = comp_raw.get("mae_global")
        detalle = comp_raw.get("detalle", [])

        col1, col2 = st.columns(2)
        col1.metric(
            "📊 Pares comparados",
            comparaciones,
            help="Cantidad de dias con prediccion y venta real." )
        col2.metric(
            "⚡ MAE Global",
            f"{mae_global:.2f} uds" if mae_global else "Sin datos",
            help="Error promedio entre prediccion y venta real." )

        if detalle:
            df_comp = pd.DataFrame(detalle)
            df_comp["fecha"] = pd.to_datetime(df_comp["fecha"])

            productos_comp = ["Todos los productos (Suma)"] + sorted(df_comp["producto_nombre"].unique().tolist())
            prod_sel = st.selectbox("Seleccionar producto para validar:", productos_comp)

            if prod_sel == "Todos los productos (Suma)":
                df_plot = df_comp.groupby("fecha").agg({"real": "sum", "predicho": "sum"}).reset_index()
                titulo_graf = "Validacion Total: Suma de todos los productos"
            else:
                df_plot = df_comp[df_comp["producto_nombre"] == prod_sel]
                titulo_graf = f"Validacion Individual: {prod_sel}"

            fig_comp = go.Figure()
            fig_comp.add_trace(go.Scatter(x=df_plot["fecha"], y=df_plot["real"],
                                           mode="lines+markers", name="Venta Real",
                                           line=dict(color="#34d399", width=3)))
            fig_comp.add_trace(go.Scatter(x=df_plot["fecha"], y=df_plot["predicho"],
                                           mode="lines+markers", name="Prediccion IA",
                                           line=dict(color="#ff6b35", width=3, dash="dot")))

            fig_comp.update_layout(
                title=titulo_graf,
                plot_bgcolor="#1e2a3a", paper_bgcolor="#1e2a3a",
                font=dict(color="#e2e8f0"),
                xaxis=dict(title="Fecha", tickformat="%d %b", type='date'),
                yaxis_title="Unidades", height=450,
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("Aun no hay suficientes pares prediccion-real.")
    except Exception as e:
        st.info(f"No se pudo cargar comparacion: {e}")

except Exception as e:
    st.error(f"Error al cargar metricas ML: {e}")