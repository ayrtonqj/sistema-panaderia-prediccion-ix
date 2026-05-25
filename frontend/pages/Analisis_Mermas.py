import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Mermas | Panadería Victoria", page_icon="📊", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.main{background:#0f1117;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#1a1f2e,#0d1117);border-right:1px solid #2d3748;}
</style>""", unsafe_allow_html=True)

API = "http://localhost:8000"

st.markdown("# 📊 Análisis de Mermas")
st.markdown("Diagnóstico de causas raíz de sobreproducción y subproducción — **Objetivo Específico 1 (OE1)**.")

st.markdown("---")

try:
    analisis = requests.get(f"{API}/mermas/analisis", timeout=8).json()
    pct = analisis.get("porcentaje_merma_global", 0)
    total_merma = analisis.get("total_unidades_merma", 0)
    por_motivo = analisis.get("por_motivo", [])
    por_producto = analisis.get("por_producto", [])

    # ── KPIs ──────────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    delta_color = "inverse" if pct > 20 else "normal"
    col1.metric("% Merma Global", f"{pct}%", delta=f"Meta: ≤20%", delta_color=delta_color)
    col2.metric("Total Unidades Merma", f"{total_merma:,.0f}")
    col3.metric("Causas identificadas", len(por_motivo))

    if pct > 20:
        st.error(f"🚨 La merma actual ({pct}%) supera el umbral objetivo del 20%. El sistema predictivo está trabajando para reducirla.")
    else:
        st.success(f"✅ La merma ({pct}%) está dentro del objetivo de investigación (≤20%).")

    st.markdown("---")
    col_l, col_r = st.columns(2)

    # ── Gráfico Pareto por motivo ─────────────────────────────────────────────
    with col_l:
        st.markdown("### Pareto de Mermas por Motivo")
        df_motivo = pd.DataFrame(por_motivo).sort_values("total_merma", ascending=False)
        df_motivo["acumulado_pct"] = (df_motivo["total_merma"].cumsum() / df_motivo["total_merma"].sum() * 100).round(1)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_motivo["motivo"], y=df_motivo["total_merma"],
            name="Merma (uds)", marker_color="#ff6b35",
            text=df_motivo["total_merma"].round(0).astype(int), textposition="outside",
        ))
        fig.add_trace(go.Scatter(
            x=df_motivo["motivo"], y=df_motivo["acumulado_pct"],
            name="% Acumulado", yaxis="y2", mode="lines+markers",
            line=dict(color="#34d399", width=2), marker=dict(size=8),
        ))
        fig.update_layout(
            yaxis=dict(title="Unidades de merma", gridcolor="#2d4a6a"),
            yaxis2=dict(title="% Acumulado", overlaying="y", side="right", range=[0, 110], gridcolor="#2d4a6a"),
            plot_bgcolor="#1e2a3a", paper_bgcolor="#1e2a3a",
            font=dict(color="#e2e8f0", family="Inter"),
            legend=dict(bgcolor="#0d1117"), height=380,
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Gráfico por producto ──────────────────────────────────────────────────
    with col_r:
        st.markdown("### Merma Total por Producto")
        df_prod = pd.DataFrame(por_producto).sort_values("total_merma", ascending=True)
        fig2 = go.Figure(go.Bar(
            x=df_prod["total_merma"].round(0).astype(int),
            y=df_prod["producto"],
            orientation="h",
            marker_color=px.colors.sequential.Oranges[3:],
            text=df_prod["total_merma"].round(0).astype(int),
            textposition="outside",
        ))
        fig2.update_layout(
            xaxis=dict(title="Unidades de merma", gridcolor="#2d4a6a"),
            yaxis=dict(title=""),
            plot_bgcolor="#1e2a3a", paper_bgcolor="#1e2a3a",
            font=dict(color="#e2e8f0", family="Inter"),
            height=380,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Tablas detalladas ─────────────────────────────────────────────────────
    st.markdown("### 📋 Detalle por motivo")
    df_m = pd.DataFrame(por_motivo)
    df_m["total_merma"] = df_m["total_merma"].round(0).astype(int)
    df_m["pct"] = (df_m["total_merma"] / df_m["total_merma"].sum() * 100).round(1).astype(str) + "%"
    df_m.columns = ["Motivo", "Frecuencia", "Total Merma (uds)", "% del Total"]
    st.dataframe(df_m, use_container_width=True, hide_index=True)

    st.markdown("### 📋 Detalle por producto")
    df_p2 = pd.DataFrame(por_producto)
    df_p2["total_merma"] = df_p2["total_merma"].round(0).astype(int)
    df_p2.columns = ["Producto", "Total Merma (uds)", "Frecuencia"]
    st.dataframe(df_p2, use_container_width=True, hide_index=True)

    # ── Últimas mermas registradas ────────────────────────────────────────────
    st.markdown("### 🕐 Últimas 20 mermas registradas")
    mermas_raw = requests.get(f"{API}/mermas/", timeout=5).json()
    if mermas_raw:
        df_mermas = pd.DataFrame(mermas_raw[-20:])
        df_mermas["cantidad_merma"] = df_mermas["cantidad_merma"].round(1)
        df_mermas = df_mermas[["producto_nombre", "fecha", "cantidad_merma", "motivo"]]
        df_mermas.columns = ["Producto", "Fecha", "Cantidad Merma", "Motivo"]
        st.dataframe(df_mermas, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error al cargar análisis de mermas: {e}")
