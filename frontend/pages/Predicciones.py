import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date

DIAS_ESP = {
    "Monday": "Lun", "Tuesday": "Mar", "Wednesday": "Mié",
    "Thursday": "Jue", "Friday": "Vie", "Saturday": "Sáb", "Sunday": "Dom"
}
DIAS_ESP_FULL = {
    "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
    "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
}

def format_fecha_es(fecha):
    dia_semana = fecha.strftime("%A")
    return fecha.strftime(f"%d/%m/%Y ({DIAS_ESP_FULL.get(dia_semana, dia_semana)})")

def format_fecha_abrev(fecha):
    return f"{DIAS_ESP.get(fecha.strftime('%A'), fecha.strftime('%A'))} {fecha.strftime('%d/%m')}"

st.set_page_config(page_title="Predicciones | Panadería Victoria", page_icon="📈", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.main{background:#0f1117;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#1a1f2e,#0d1117);border-right:1px solid #2d3748;}
</style>""", unsafe_allow_html=True)

API = "http://localhost:8000"

st.markdown("# 📈 Predicciones de Demanda")
st.markdown("Pronóstico de ventas para los próximos 7 días generado por el modelo **Random Forest** con clima real de Pacasmayo.")

col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])

with col_btn1:
    if st.button("🔄 Generar nuevas predicciones", use_container_width=True):
        with st.spinner("Ejecutando modelo ML..."):
            try:
                r = requests.post(f"{API}/predicciones/generar?n_dias=7", timeout=30)
                if r.status_code == 200:
                    st.success(f"✅ {r.json().get('total_predicciones', 0)} predicciones generadas con clima real.")
                else:
                    st.error(f"Error: {r.text}")
            except Exception as e:
                st.error(f"No se pudo conectar: {e}")

with col_btn2:
    if st.button("🌤️ Sincronizar clima", use_container_width=True):
        with st.spinner("Consultando Open-Meteo..."):
            try:
                r = requests.post(f"{API}/clima/sincronizar?dias=7", timeout=15)
                if r.status_code == 200:
                    d = r.json()
                    st.success(f"✅ Clima actualizado: {d['registros_insertados']} nuevos, {d['registros_actualizados']} actualizados.")
                else:
                    st.error(f"Error: {r.text}")
            except Exception as e:
                st.error(f"Error al sincronizar clima: {e}")

st.markdown("---")

# ── Cargar predicciones ───────────────────────────────────────────────────────
try:
    pred_raw = requests.get(f"{API}/predicciones/", timeout=5).json()
    if not pred_raw:
        st.warning("No hay predicciones guardadas. Haz clic en 'Generar nuevas predicciones'.")
        st.stop()

    df_pred = pd.DataFrame(pred_raw)
    df_pred["fecha_proyectada"] = pd.to_datetime(df_pred["fecha_proyectada"])

    # Cargar nombres de productos
    productos_raw = requests.get(f"{API}/productos/", timeout=5).json()
    prod_map = {p["id"]: p["nombre"] for p in productos_raw}
    df_pred["producto"] = df_pred["producto_id"].map(prod_map)

    # ── Filtros ───────────────────────────────────────────────────────────────
    productos_lista = sorted(df_pred["producto"].dropna().unique())
    sel_productos = st.multiselect("Filtrar productos:", productos_lista, default=productos_lista[:4])
    df_filtrado = df_pred[df_pred["producto"].isin(sel_productos)] if sel_productos else df_pred

    # ── Gráfico principal: línea de predicciones ──────────────────────────────
    fig = go.Figure()
    colores = px.colors.qualitative.Set2

    for i, prod in enumerate(df_filtrado["producto"].unique()):
        df_p = df_filtrado[df_filtrado["producto"] == prod].sort_values("fecha_proyectada")
        df_p = df_p.copy()
        df_p["fecha_label"] = df_p["fecha_proyectada"].apply(format_fecha_abrev)
        fig.add_trace(go.Bar(
            name=prod,
            x=df_p["fecha_label"],
            y=df_p["demanda_estimada"],
            marker_color=colores[i % len(colores)],
            text=df_p["demanda_estimada"].round(0).astype(int),
            textposition="outside",
        ))

    fig.update_layout(
        title="Demanda Estimada por Producto — Próximos 7 días",
        barmode="group",
        plot_bgcolor="#1e2a3a",
        paper_bgcolor="#1e2a3a",
        font=dict(color="#e2e8f0", family="Inter"),
        xaxis=dict(gridcolor="#2d4a6a", title="Fecha"),
        yaxis=dict(gridcolor="#2d4a6a", title="Unidades a Producir"),
        legend=dict(bgcolor="#0d1117", bordercolor="#2d4a6a"),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Tabla detallada ───────────────────────────────────────────────────────
    st.markdown("### 📋 Detalle de predicciones")
    df_tabla = df_filtrado[["producto", "fecha_proyectada", "demanda_estimada", "confianza_prediccion"]].copy()
    df_tabla["fecha_proyectada"] = df_tabla["fecha_proyectada"].apply(format_fecha_es)
    df_tabla["demanda_estimada"] = df_tabla["demanda_estimada"].astype(int)
    df_tabla["confianza_prediccion"] = (df_tabla["confianza_prediccion"] * 100).round(1).astype(str) + "%"
    df_tabla.columns = ["Producto", "Fecha", "Unidades Estimadas", "Confianza Modelo"]
    st.dataframe(df_tabla, use_container_width=True, hide_index=True)

    # ── Resumen por producto ──────────────────────────────────────────────────
    st.markdown("### 📦 Total a producir esta semana")
    resumen = df_filtrado.groupby("producto")["demanda_estimada"].sum().reset_index()
    resumen.columns = ["Producto", "Total 7 días"]
    resumen["Total 7 días"] = resumen["Total 7 días"].astype(int)
    resumen = resumen.sort_values("Total 7 días", ascending=False)

    fig2 = px.pie(resumen, values="Total 7 días", names="Producto",
                  title="Distribución de producción semanal",
                  color_discrete_sequence=px.colors.qualitative.Set2,
                  hole=0.4)
    fig2.update_layout(paper_bgcolor="#1e2a3a", font=dict(color="#e2e8f0", family="Inter"))
    st.plotly_chart(fig2, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar predicciones: {e}")
