import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus.flowables import KeepTogether
import plotly.io as pio
import base64

API = "http://localhost:8000"


def obtener_imagen_grafico(fig):
    try:
        fig_pdf = go.Figure(fig)
        fig_pdf.update_layout(
            template="plotly_white",
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(color="black", size=14),
            margin=dict(l=100, r=50, t=80, b=50),
            title=dict(font=dict(size=22))
        )
        if hasattr(fig_pdf.data[0], 'orientation') and fig_pdf.data[0].orientation == 'h':
            fig_pdf.update_layout(yaxis=dict(tickfont=dict(size=12)))
        img_bytes = pio.to_image(fig_pdf, format="png", width=1200, height=600, scale=2, engine="kaleido")
        return img_bytes
    except Exception as e:
        return None


def generar_reporte_pdf(total_ingresos, total_costo_prod, total_perdida_merma, utilidad_estimada,
                        resumen_prod, fecha_inicio, fecha_fin, img_prod, img_line):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'],
                                  fontSize=18, textColor=colors.HexColor('#ff6b35'),
                                  spaceAfter=10, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                     fontSize=10, textColor=colors.HexColor('#666666'),
                                     alignment=TA_CENTER)
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'],
                               fontSize=13, textColor=colors.HexColor('#1e2a3a'),
                               spaceBefore=15, spaceAfter=8)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=9)
    money_style = ParagraphStyle('Money', parent=styles['Normal'],
                                  fontSize=11, textColor=colors.HexColor('#27ae60'),
                                  alignment=TA_RIGHT, fontName='Helvetica-Bold')

    elements = []

    elements.append(Paragraph("Reportes Financieros - Panaderia Victoria", title_style))
    elements.append(Paragraph(f"Periodo: {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}", subtitle_style))
    elements.append(Paragraph(f"Generado: {date.today().strftime('%d/%m/%Y %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 10*mm))

    kpi_data = [
        ['Ingresos Totales', 'Costo Produccion', 'Perdida por Merma', 'Utilidad Bruta Est.'],
        [f'S/ {total_ingresos:,.2f}', f'S/ {total_costo_prod:,.2f}',
         f'S/ {total_perdida_merma:,.2f}', f'S/ {utilidad_estimada:,.2f}']
    ]
    kpi_table = Table(kpi_data, colWidths=[40*mm, 40*mm, 40*mm, 40*mm])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e2a3a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f8f9fa')),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#1e2a3a'), colors.HexColor('#f8f9fa')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#2d4a6a')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 8*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2d4a6a')))
    elements.append(Spacer(1, 5*mm))

    if img_prod:
        elements.append(Paragraph("Ingresos por Producto", h2_style))
        img_obj = Image(BytesIO(img_prod), width=165*mm, height=80*mm)
        elements.append(img_obj)
        elements.append(Spacer(1, 5*mm))

    if img_line:
        elements.append(Paragraph("Evolucion de Ingresos", h2_style))
        img_obj2 = Image(BytesIO(img_line), width=165*mm, height=65*mm)
        elements.append(img_obj2)
        elements.append(Spacer(1, 5*mm))

    table_data = [['Producto', 'Uds Vendidas', 'Ingreso (S/)', 'Costo (S/)', 'Perdida Merma (S/)', 'Margen (S/)']]
    for _, r in resumen_prod.iterrows():
        table_data.append([
            str(r['Producto'])[:30],
            f"{r['Uds Vendidas']:.0f}",
            f"S/ {r['Ingreso (S/)']:,.2f}",
            f"S/ {r['Costo Prod (S/)']:,.2f}",
            f"S/ {r['Perdida Merma (S/)']:,.2f}",
            f"S/ {r['Margen (S/)']:,.2f}",
        ])

    detail_table = Table(table_data, colWidths=[38*mm, 18*mm, 28*mm, 26*mm, 30*mm, 25*mm])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e2a3a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#2d4a6a')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    grupo_tabla = KeepTogether([
        Paragraph("Detalle por Producto", h2_style),
        detail_table,
        Spacer(1, 10*mm)
    ])
    elements.append(grupo_tabla)

    elements.append(Paragraph("Sistema Predictivo - Panaderia Victoria", subtitle_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


st.set_page_config(page_title="Reportes Financieros | Panaderia Victoria", page_icon="💰", layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.main{background:#0f1117;}
.stMetric{background:#1e2a3a; padding: 20px; border-radius: 10px; border: 1px solid #2d4a6a;}
</style>""", unsafe_allow_html=True)

st.title("💰 Reportes Financieros")
st.markdown("Analisis de ingresos, costos de produccion y perdidas por merma.")

try:
    ventas_raw = requests.get(f"{API}/ventas/", timeout=5).json()
    productos_raw = requests.get(f"{API}/productos/", timeout=5).json()
    mermas_raw = requests.get(f"{API}/mermas/", timeout=5).json()

    if not ventas_raw:
        st.warning("No hay datos de ventas registrados para generar reportes.")
        st.stop()

    prod_info = {p['id']: {'nombre': p['nombre'], 'precio': p['precio'], 'costo': p['costo']} for p in productos_raw}

    df_v = pd.DataFrame(ventas_raw)
    df_v['precio'] = df_v['producto_id'].apply(lambda x: prod_info.get(x, {}).get('precio', 0))
    df_v['costo_unit'] = df_v['producto_id'].apply(lambda x: prod_info.get(x, {}).get('costo', 0))
    df_v['ingreso'] = df_v['cantidad_vendida'] * df_v['precio']
    df_v['costo_prod'] = df_v['cantidad_producida'].fillna(0) * df_v['costo_unit']
    df_v['fecha'] = pd.to_datetime(df_v['fecha'])

    if mermas_raw:
        df_m = pd.DataFrame(mermas_raw)
        df_m['costo_unit'] = df_m['producto_id'].apply(lambda x: prod_info.get(x, {}).get('costo', 0))
        df_m['perdida_economica'] = df_m['cantidad_merma'] * df_m['costo_unit']
        df_m['fecha'] = pd.to_datetime(df_m['fecha'])
    else:
        df_m = pd.DataFrame(columns=['producto_id', 'producto_nombre', 'cantidad_merma', 'perdida_economica', 'fecha'])

    fecha_min = df_v['fecha'].min().date() if not df_v.empty else date.today()
    fecha_max = df_v['fecha'].max().date() if not df_v.empty else date.today()

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        fecha_inicio = st.date_input("Desde:", fecha_min, min_value=fecha_min, max_value=fecha_max)
    with col_f2:
        fecha_fin = st.date_input("Hasta:", fecha_max, min_value=fecha_min, max_value=fecha_max)
    with col_f3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Actualizar Reporte"):
            st.rerun()

    df_v = df_v[(df_v['fecha'].dt.date >= fecha_inicio) & (df_v['fecha'].dt.date <= fecha_fin)]
    df_m = df_m[(df_m['fecha'].dt.date >= fecha_inicio) & (df_m['fecha'].dt.date <= fecha_fin)]

    if df_v.empty:
        st.warning(f"No hay datos de ventas entre {fecha_inicio} y {fecha_fin}.")
        st.stop()

    st.markdown(f"**Mostrando datos del {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}**")
    st.markdown("---")

    total_ingresos = df_v['ingreso'].sum()
    total_costo_prod = df_v['costo_prod'].sum()
    total_perdida_merma = df_m['perdida_economica'].sum()
    utilidad_estimada = total_ingresos - total_costo_prod

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ingresos Totales", f"S/ {total_ingresos:,.2f}")
    c2.metric("Costo Produccion", f"S/ {total_costo_prod:,.2f}")
    c3.metric("Perdida por Merma", f"S/ {total_perdida_merma:,.2f}", delta_color="inverse")
    c4.metric("Utilidad Bruta Est.", f"S/ {utilidad_estimada:,.2f}")

    st.markdown("---")

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("### Ingresos por Producto")
        df_prod_ing = df_v.groupby('producto_nombre')['ingreso'].sum().reset_index().sort_values('ingreso', ascending=True)
        fig_prod = px.bar(df_prod_ing, x='ingreso', y='producto_nombre', orientation='h',
                          color='ingreso', color_continuous_scale='Viridis')
        fig_prod.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"))
        st.plotly_chart(fig_prod, use_container_width=True)

    with col_r:
        st.markdown("### Evolucion de Ingresos (S/)")
        df_diario = df_v.groupby('fecha')['ingreso'].sum().reset_index()
        fig_line = px.line(df_diario, x='fecha', y='ingreso', markers=True)
        fig_line.update_traces(line_color='#34d399')
        fig_line.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"))
        st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("### 📋 Detalle Financiero por Producto")
    resumen_prod = df_v.groupby('producto_nombre').agg({
        'cantidad_vendida': 'sum',
        'ingreso': 'sum',
        'costo_prod': 'sum'
    }).reset_index()

    resumen_merma = df_m.groupby('producto_nombre')['perdida_economica'].sum().reset_index()
    resumen_prod = pd.merge(resumen_prod, resumen_merma, on='producto_nombre', how='left').fillna(0)
    resumen_prod['Margen Est.'] = resumen_prod['ingreso'] - resumen_prod['costo_prod']
    resumen_prod.columns = ['Producto', 'Uds Vendidas', 'Ingreso (S/)', 'Costo Prod (S/)', 'Perdida Merma (S/)', 'Margen (S/)']

    st.dataframe(resumen_prod.style.format({
        'Ingreso (S/)': '{:,.2f}',
        'Costo Prod (S/)': '{:,.2f}',
        'Perdida Merma (S/)': '{:,.2f}',
        'Margen (S/)': '{:,.2f}'
    }), use_container_width=True, hide_index=True)

    st.markdown("---")
    col_btn, _ = st.columns([1, 3])
    with col_btn:
        if st.button("📄 Exportar Reporte a PDF", use_container_width=True):
            with st.spinner("Generando PDF..."):
                img_prod = obtener_imagen_grafico(fig_prod)
                img_line = obtener_imagen_grafico(fig_line)
                pdf_bytes = generar_reporte_pdf(
                    total_ingresos, total_costo_prod, total_perdida_merma, utilidad_estimada,
                    resumen_prod, fecha_inicio, fecha_fin, img_prod, img_line
                )
                if pdf_bytes:
                    st.download_button(
                        label="📥 Descargar PDF",
                        data=pdf_bytes,
                        file_name=f"reporte_financiero_{date.today()}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                else:
                    st.error("Error al generar PDF")

except Exception as e:
    st.error(f"Error generando reportes: {e}")