import streamlit as st
import requests
import pandas as pd
from datetime import date

st.set_page_config(page_title="Órdenes de Compra | Panadería Victoria", page_icon="🛒", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.main{background:#0f1117;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#1a1f2e,#0d1117);border-right:1px solid #2d3748;}
</style>""", unsafe_allow_html=True)

API = "http://localhost:8000"

st.markdown("# 🛒 Órdenes de Compra")
st.markdown("Gestión de órdenes de reposición de insumos. Automatizable con **n8n**.")

tab1, tab2 = st.tabs(["📋 Ver órdenes", "➕ Crear orden"])

with tab1:
    try:
        r = requests.get(f"{API}/ordenes-compra/", timeout=5)
        if r.status_code != 200:
            st.error(f"Error del servidor: {r.status_code}")
            st.stop()
        ordenes_raw = r.json()
        if not ordenes_raw:
            st.info("No hay órdenes de compra registradas.")
        else:
            df_ord = pd.DataFrame(ordenes_raw)

            # KPIs
            col1, col2, col3 = st.columns(3)
            col1.metric("Total órdenes", len(df_ord))
            col2.metric("Pendientes", (df_ord["estado"] == "pendiente").sum())
            col3.metric("Recibidas", (df_ord["estado"] == "recibido").sum())

            # Filtro por estado
            estado_filtro = st.selectbox("Filtrar por estado:", ["Todos", "pendiente", "recibido", "cancelado"])
            df_show = df_ord if estado_filtro == "Todos" else df_ord[df_ord["estado"] == estado_filtro]

            # Tabla coloreada con estado
            def color_estado(val):
                colors = {"pendiente": "background-color:#7c3aed;color:white",
                          "recibido": "background-color:#059669;color:white",
                          "cancelado": "background-color:#dc2626;color:white"}
                return colors.get(val, "")

            st.dataframe(
                df_show[["id", "proveedor_nombre", "insumo_nombre", "fecha_orden", "cantidad", "precio_unitario", "estado"]].rename(
                    columns={"id": "ID", "proveedor_nombre": "Proveedor", "insumo_nombre": "Insumo",
                             "fecha_orden": "Fecha", "cantidad": "Cantidad", "precio_unitario": "P. Unitario", "estado": "Estado"}
                ),
                use_container_width=True, hide_index=True
            )

            # Actualizar estado
            st.markdown("### 🔄 Actualizar estado de una orden")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                orden_id = st.number_input("ID de la orden:", min_value=1, step=1)
            with col_b:
                nuevo_estado = st.selectbox("Nuevo estado:", ["pendiente", "recibido", "cancelado"])
            with col_c:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Actualizar", use_container_width=True):
                    r = requests.put(f"{API}/ordenes-compra/{orden_id}/estado?estado={nuevo_estado}", timeout=5)
                    if r.status_code == 200:
                        st.success(f"✅ Orden #{orden_id} actualizada a '{nuevo_estado}'")
                        st.rerun()
                    else:
                        st.error(f"Error: {r.text}")

    except Exception as e:
        st.error(f"Error al cargar órdenes: {e}")

with tab2:
    st.markdown("### Nueva Orden de Compra")
    try:
        r_prov = requests.get(f"{API}/proveedores/", timeout=5)
        r_insu = requests.get(f"{API}/insumos/", timeout=5)
        if r_prov.status_code != 200 or r_insu.status_code != 200:
            st.error("Error al cargar proveedores o insumos")
            st.stop()
        proveedores_raw = r_prov.json()
        insumos_raw = r_insu.json()

        prov_map = {p["nombre"]: p["id"] for p in proveedores_raw}
        insu_map = {i["nombre"]: i["id"] for i in insumos_raw}

        col1, col2 = st.columns(2)
        with col1:
            proveedor_sel = st.selectbox("Proveedor:", list(prov_map.keys()))
            insumo_sel = st.selectbox("Insumo:", list(insu_map.keys()))
            fecha_orden = st.date_input("Fecha de orden:", value=date.today())
        with col2:
            cantidad = st.number_input("Cantidad a pedir:", min_value=0.1, step=1.0)
            precio_unitario = st.number_input("Precio unitario (S/):", min_value=0.0, step=0.1)
            estado_inicial = st.selectbox("Estado inicial:", ["pendiente", "recibido"])

        if precio_unitario > 0 and cantidad > 0:
            st.info(f"💰 **Costo total estimado:** S/ {cantidad * precio_unitario:,.2f}")

        if st.button("✅ Crear orden de compra", use_container_width=True):
            payload = {
                "proveedor_id": prov_map[proveedor_sel],
                "insumo_id": insu_map[insumo_sel],
                "fecha_orden": str(fecha_orden),
                "cantidad": cantidad,
                "precio_unitario": precio_unitario if precio_unitario > 0 else None,
                "estado": estado_inicial,
            }
            r = requests.post(f"{API}/ordenes-compra/", json=payload, timeout=5)
            if r.status_code in [200, 201]:
                st.success("✅ Orden creada exitosamente.")
                st.rerun()
            else:
                st.error(f"Error: {r.text}")

    except Exception as e:
        st.error(f"Error al cargar formulario: {e}")
