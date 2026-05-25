import streamlit as st
import requests
import plotly.express as px
import pandas as pd
from datetime import date

st.set_page_config(page_title="Registro Diario | Panadería Victoria", page_icon="✏️", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.main{background:#0f1117;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#1a1f2e,#0d1117);border-right:1px solid #2d3748;}
</style>""", unsafe_allow_html=True)

API = "http://localhost:8000"

st.markdown("# ✏️ Registro Diario")
st.markdown("Ingresa las ventas del día. El sistema calcula las mermas y descuenta insumos **automáticamente**.")

# Lista unificada de motivos (para asegurar consistencia en la BD)
MOTIVOS_MERMA = [
    "Sobreproducción", 
    "Caducidad", 
    "Falla en cocción", 
    "Daño en manipulación", 
    "Devolución cliente", 
    "Calidad insuficiente",
    "Otro"
]

tab_venta, tab_merma, tab_historial = st.tabs(["💰 Registrar Venta", "🗑️ Registrar Merma Manual", "📋 Historial"])

with tab_venta:
    st.markdown("### Nueva Venta")
    st.caption("Al ingresar **Cantidad Producida**, el sistema activa 2 automatismos: ① genera la merma por sobreproducción, ② descuenta los insumos del inventario.")

    try:
        productos_raw = requests.get(f"{API}/productos/", timeout=5).json()
        opciones = {p["nombre"]: p["id"] for p in productos_raw}

        col1, col2 = st.columns(2)
        with col1:
            producto_sel = st.selectbox("Producto:", list(opciones.keys()), key="sel_venta")
            fecha_v = st.date_input("Fecha:", value=date.today(), key="fecha_venta")
        with col2:
            cantidad_v = st.number_input("Cantidad vendida:", min_value=0.0, step=1.0, key="qty_venta")
            cantidad_producida = st.number_input(
                "Cantidad producida:",
                min_value=0.0, step=1.0, key="qty_prod",
                help="Si produjiste mas de lo que vendiste, el sistema calcula la merma automaticamente."
            )

        # Vista previa de merma y selección de motivo
        motivo_merma_auto = "Sobreproducción"
        if cantidad_producida > 0 and cantidad_v > 0:
            if cantidad_producida > cantidad_v:
                excedente = cantidad_producida - cantidad_v
                st.warning(f"⚠️ Se generará automáticamente una merma de **{excedente:.0f} unidades**.")
                motivo_merma_auto = st.selectbox(
                    "Motivo del excedente:",
                    MOTIVOS_MERMA,
                    index=0, # Por defecto Sobreproducción
                    help="¿Por qué sobró este producto hoy?"
                )
            elif cantidad_producida < cantidad_v:
                st.error(f"⚠️ Produciste menos de lo que vendiste ({cantidad_producida:.0f} < {cantidad_v:.0f}). Verifica los datos.")
            else:
                st.success("✅ Producción exacta — sin merma por sobreproducción.")

        # Prediccion del modelo para esa fecha
        try:
            pred_hoy = requests.get(f"{API}/predicciones/", timeout=3).json()
            prod_id_sel = opciones[producto_sel]
            pred_prod = [p for p in pred_hoy if p["producto_id"] == prod_id_sel and p["fecha_proyectada"] == str(fecha_v)]
            if pred_prod:
                pred_val = pred_prod[0]["demanda_estimada"]
                st.info(f"Prediccion del modelo para {producto_sel} el {fecha_v}: {pred_val:.0f} unidades")
        except Exception:
            pass

        if st.button("Registrar venta", use_container_width=True, key="btn_venta"):
            if cantidad_v <= 0:
                st.error("La cantidad vendida debe ser mayor a 0.")
            else:
                payload = {
                    "producto_id": opciones[producto_sel],
                    "fecha": str(fecha_v),
                    "cantidad_vendida": cantidad_v,
                    "cantidad_producida": cantidad_producida if cantidad_producida > 0 else None,
                    "motivo_merma": motivo_merma_auto
                }
                r = requests.post(f"{API}/ventas/", json=payload, timeout=5)
                if r.status_code in [200, 201]:
                    data = r.json()
                    st.success(f"Venta de {cantidad_v:.0f} uds de '{producto_sel}' registrada correctamente.")

                    # Mostrar resultado de automatismos
                    merma_auto = data.get("merma_auto_generada")
                    insumos_desc = data.get("insumos_descontados", [])

                    if merma_auto:
                        st.warning(f"🗑️ Merma automática creada: {merma_auto} unidades")

                    if insumos_desc:
                        st.markdown("**Insumos descontados del stock:**")
                        for item in insumos_desc:
                            st.markdown(f"- **{item['insumo']}**: -{item['consumo']:.3f} | quedan {item['stock_restante']:.3f}")
                    elif cantidad_producida > 0:
                        st.info("(No hay ficha tecnica registrada para este producto aun.)")
                else:
                    st.error(f"Error al registrar: {r.text}")

    except Exception as e:
        st.error(f"Error: {e}")

with tab_merma:
    st.markdown("### Merma Manual")
    st.caption("Usa esto para mermas que NO son por sobreproduccion (pan quemado, devoluciones, accidentes).")
    MOTIVOS = ["Caducidad", "Dano en manipulacion", "Falla en coccion", "Devolucion cliente", "Otro"]
    try:
        productos_raw = requests.get(f"{API}/productos/", timeout=5).json()
        opciones_m = {p["nombre"]: p["id"] for p in productos_raw}

        col1, col2 = st.columns(2)
        with col1:
            producto_m = st.selectbox("Producto:", list(opciones_m.keys()), key="sel_merma")
            fecha_m = st.date_input("Fecha:", value=date.today(), key="fecha_merma")
        with col2:
            cantidad_m = st.number_input("Cantidad de merma:", min_value=0.0, step=1.0, key="qty_merma")
            motivo = st.selectbox("Motivo:", MOTIVOS_MERMA, key="motivo_merma")

        if st.button("Registrar merma", use_container_width=True, key="btn_merma"):
            if cantidad_m <= 0:
                st.error("La cantidad debe ser mayor a 0.")
            else:
                payload = {
                    "producto_id": opciones_m[producto_m],
                    "fecha": str(fecha_m),
                    "cantidad_merma": cantidad_m,
                    "motivo": motivo,
                }
                r = requests.post(f"{API}/mermas/", json=payload, timeout=5)
                if r.status_code in [200, 201]:
                    st.success(f"Merma de {cantidad_m:.0f} uds de '{producto_m}' registrada (motivo: {motivo}).")
                else:
                    st.error(f"Error: {r.text}")

    except Exception as e:
        st.error(f"Error: {e}")

with tab_historial:
    st.markdown("### Historial reciente")
    tab_a, tab_b = st.tabs(["Ventas", "Mermas"])

    with tab_a:
        try:
            ventas = requests.get(f"{API}/ventas/", timeout=5).json()
            if ventas:
                df_v = pd.DataFrame(ventas)
                # Ordenar por fecha descendente
                df_v = df_v.sort_values(by="fecha", ascending=False).head(20)
                
                for _, row in df_v.iterrows():
                    with st.expander(f"💰 {row['fecha']} - {row['producto_nombre']} ({int(row['cantidad_vendida'])} uds)"):
                        col_info, col_del = st.columns([4, 1])
                        col_info.write(f"**Producido:** {row['cantidad_producida']} | **ID:** {row['id']}")
                        if col_del.button("🗑️ Eliminar", key=f"del_v_{row['id']}"):
                            res = requests.delete(f"{API}/ventas/{row['id']}")
                            if res.status_code == 200:
                                st.success("Eliminado. Recargando...")
                                st.rerun()
                            else:
                                st.error("No se pudo eliminar")
                
                df_v["fecha"] = pd.to_datetime(df_v["fecha"])
                df_agg = df_v.groupby("fecha")["cantidad_vendida"].sum().reset_index()
                fig = px.line(df_agg, x="fecha", y="cantidad_vendida", title="Tendencia de ventas recientes")
                fig.update_layout(plot_bgcolor="#1e2a3a", paper_bgcolor="#1e2a3a", font=dict(color="#e2e8f0"), height=250)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay ventas registradas.")
        except Exception as e:
            st.error(f"Error: {e}")

    with tab_b:
        try:
            mermas = requests.get(f"{API}/mermas/", timeout=5).json()
            if mermas:
                df_m = pd.DataFrame(mermas)
                df_m = df_m.sort_values(by="fecha", ascending=False).head(20)

                for _, row in df_m.iterrows():
                    with st.expander(f"🗑️ {row['fecha']} - {row['producto_nombre']} ({int(row['cantidad_merma'])} uds)"):
                        col_info, col_del = st.columns([4, 1])
                        col_info.write(f"**Motivo:** {row['motivo']} | **ID:** {row['id']}")
                        if col_del.button("🗑️ Eliminar", key=f"del_m_{row['id']}"):
                            res = requests.delete(f"{API}/mermas/{row['id']}")
                            if res.status_code == 200:
                                st.success("Eliminado. Recargando...")
                                st.rerun()
                            else:
                                st.error("No se pudo eliminar")
            else:
                st.info("No hay mermas registradas.")
        except Exception as e:
            st.error(f"Error: {e}")
