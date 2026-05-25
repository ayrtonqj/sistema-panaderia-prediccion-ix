import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Inventario | Panadería Victoria", page_icon="🏪", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.main{background:#0f1117;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#1a1f2e,#0d1117);border-right:1px solid #2d3748;}
.stock-ok{background:rgba(52,211,153,0.1);border:1px solid #34d399;border-radius:8px;padding:0.6rem 1rem;color:#6ee7b7;margin:0.3rem 0;}
.stock-alerta{background:rgba(248,113,113,0.1);border:1px solid #f87171;border-radius:8px;padding:0.6rem 1rem;color:#fca5a5;margin:0.3rem 0;}
</style>""", unsafe_allow_html=True)

API = "http://localhost:8000"

st.markdown("# 🏪 Gestión de Inventario")
st.markdown("Estado del stock de insumos críticos y alertas de reposición.")

try:
    # ── Productos con precios ───────────────────────────────────────────────────
    productos_raw = requests.get(f"{API}/productos/", timeout=5).json()
    if productos_raw:
        df_prod = pd.DataFrame(productos_raw)
        df_prod["margen_%"] = ((df_prod["precio"] - df_prod["costo"]) / df_prod["costo"] * 100).round(1)

        st.markdown("### 🍞 Productos — Precios y Costos")
        st.dataframe(
            df_prod[["nombre", "categoria", "precio", "costo", "margen_%"]],
            column_config={
                "nombre": "Producto",
                "categoria": "Categoría",
                "precio": st.column_config.NumberColumn("Precio Venta", format="S/ %.2f"),
                "costo": st.column_config.NumberColumn("Costo", format="S/ %.2f"),
                "margen_%": st.column_config.NumberColumn("Margen %", format="%.1f%%"),
            },
            use_container_width=True,
            hide_index=True,
        )
        st.markdown("---")

    alertas_raw = requests.get(f"{API}/insumos/alertas/", timeout=5).json()
    proveedores_raw = requests.get(f"{API}/proveedores/", timeout=5).json()
    prov_map = {p["id"]: p["nombre"] for p in proveedores_raw}

    n_ok = sum(1 for a in alertas_raw if not a["necesita_reorden"])
    n_alerta = sum(1 for a in alertas_raw if a["necesita_reorden"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Insumos", len(alertas_raw))
    col2.metric("Stock OK", n_ok, delta=None)
    col3.metric("Bajo Stock Mínimo", n_alerta, delta=f"{'🚨 Reorden urgente' if n_alerta > 0 else 'OK'}", delta_color="inverse" if n_alerta > 0 else "normal")

    st.markdown("---")
    st.markdown("### 🚦 Estado de Stock por Insumo")

    for insumo in alertas_raw:
        pct = (insumo["stock_actual"] / insumo["stock_minimo"] * 100) if insumo["stock_minimo"] > 0 else 100
        color = "#f87171" if insumo["necesita_reorden"] else "#34d399"
        icono = "🔴" if insumo["necesita_reorden"] else "🟢"
        proveedor_nombre = prov_map.get(insumo.get("proveedor_id"), "Sin proveedor asignado")

        with st.expander(f"{icono} {insumo['nombre']} — {insumo['stock_actual']} / {insumo['stock_minimo']} {insumo['unidad_medida']}"):
            col_a, col_b = st.columns([2, 1])
            with col_a:
                fig = go.Figure(go.Bar(
                    x=[insumo["stock_actual"]], y=[insumo["nombre"]],
                    orientation="h", marker_color=color,
                    text=[f"{insumo['stock_actual']} {insumo['unidad_medida']}"],
                    textposition="inside",
                ))
                fig.add_vline(x=insumo["stock_minimo"], line_color="#f59e0b", line_dash="dash",
                              annotation_text="Stock mínimo", annotation_font_color="#f59e0b")
                fig.update_layout(
                    xaxis=dict(title=insumo["unidad_medida"], gridcolor="#2d4a6a"),
                    yaxis=dict(showticklabels=False),
                    plot_bgcolor="#1e2a3a", paper_bgcolor="#1e2a3a",
                    font=dict(color="#e2e8f0"), height=120, margin=dict(l=10, r=10, t=10, b=30),
                )
                st.plotly_chart(fig, use_container_width=True)
            with col_b:
                st.markdown(f"**Proveedor:** {proveedor_nombre}")
                st.markdown(f"**Stock actual:** {insumo['stock_actual']} {insumo['unidad_medida']}")
                st.markdown(f"**Stock mínimo:** {insumo['stock_minimo']} {insumo['unidad_medida']}")
                if insumo["necesita_reorden"]:
                    deficit = insumo["stock_minimo"] - insumo["stock_actual"]
                    st.error(f"⚠️ Déficit: {deficit:.1f} {insumo['unidad_medida']}")

    # ── Actualizar stock manualmente ──────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ✏️ Actualizar Stock de un Insumo")
    insumos_nombres = {i["nombre"]: i["id"] for i in alertas_raw}
    sel = st.selectbox("Seleccionar insumo:", list(insumos_nombres.keys()))
    nuevo_stock = st.number_input("Nuevo stock actual:", min_value=0.0, step=1.0)
    if st.button("Actualizar stock", use_container_width=False):
        insumo_id = insumos_nombres[sel]
        r = requests.put(f"{API}/insumos/{insumo_id}", json={"stock_actual": nuevo_stock}, timeout=5)
        if r.status_code == 200:
            st.success(f"✅ Stock de {sel} actualizado a {nuevo_stock}")
            st.rerun()
        else:
            st.error(f"Error: {r.text}")

except Exception as e:
    st.error(f"Error al cargar inventario: {e}")
