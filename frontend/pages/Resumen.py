import streamlit as st
import requests
import pandas as pd
from datetime import date

API = "http://localhost:8000"

st.title("🏠 Dashboard Panaderia Victoria")
st.markdown("Bienvenido al sistema de gestion predictiva. Selecciona una opcion en el menu lateral.")

try:
    resumen = requests.get(f"{API}/dashboard/resumen", timeout=5).json()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "📦 Ventas Hoy",
        f"{resumen['ventas_hoy']:.0f} uds",
        help="Cantidad total de productos vendidos hoy segun el registro diario."
    )
    col2.metric(
        "⚠️ Mermas Hoy",
        f"{resumen['mermas_hoy']:.0f} uds",
        help="Unidades perdidas hoy (vencidos, roturas, exceso). Incluye todos los motivos registrados."
    )

    pct = resumen['pct_merma_30d']
    col3.metric(
        "📊 % Merma (30d)",
        f"{pct}%",
        delta="Meta: <20%",
        delta_color="inverse" if pct > 20 else "normal",
        help="Porcentaje de productos perdidos en los ultimos 30 dias. Meta: menos del 20%."
    )
    col4.metric(
        "🔴 Insumos en Alerta",
        resumen['insumos_bajo_stock'],
        help="Insumos cuyo stock esta por debajo del minimo. Hay que ordenar pronto."
    )

    st.markdown("---")

    c_l, c_r = st.columns(2)

    with c_l:
        st.subheader("🔮 Produccion sugerida (Prox. 7 dias)")
        st.caption("Cantidad estimada que deberias producir segun el clima y el calendario.")
        df_prod = pd.DataFrame(resumen['prediccion_semana'])
        if not df_prod.empty:
            st.bar_chart(df_prod.set_index('producto'))
        else:
            st.info("No hay predicciones generadas aun. Ve a Predicciones para generarlas.")

    with c_r:
        st.subheader("📋 Resumen de Operaciones")
        st.write(f"**Ordenes pendientes:** {resumen['ordenes_pendientes']}")
        st.caption("Ordenes que aun no han sido entregadas por el proveedor.")
        st.write(f"**Fecha:** {date.today()}")
        st.write("")

        if st.button("📝 Ir a Registro Diario", use_container_width=True):
            st.switch_page("pages/Registro_Diario.py")
        if st.button("💰 Ver Reportes Financieros", use_container_width=True):
            st.switch_page("pages/Reportes_Financieros.py")

except Exception:
    st.error("⚠️ No se puede conectar con el servidor. Verifica que este encendido.")