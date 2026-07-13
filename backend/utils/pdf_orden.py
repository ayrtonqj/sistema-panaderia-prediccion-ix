from fpdf import FPDF
import os
from datetime import date

FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "venv", "Lib", "site-packages", "fpdf", "font")
DEJAVU_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "venv", "Lib", "site-packages", "fpdf", "font")

def sanitize(s):
    if s is None:
        return ""
    return str(s).replace("\u2014", "-").replace("\u2013", "-").replace("\u00e1", "a").replace("\u00e9", "e").replace("\u00ed", "i").replace("\u00f3", "o").replace("\u00fa", "u").replace("\u00f1", "n").replace("\u00d1", "N").replace("\u00fc", "u")


class OrdenPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "Panaderia Victoria - Sistema Predictivo", align="C")
        self.ln(4)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Generado: {date.today().strftime('%d/%m/%Y %H:%M')} | Pag {self.page_no()}/{{nb}}", align="C")


def generar_pdf_orden(orden_data: dict) -> bytes:
    pdf = OrdenPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(30, 60, 114)
    pdf.cell(0, 12, "ORDEN DE COMPRA", align="C")
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, sanitize(f"# {orden_data.get('id', '-')}"), align="C")
    pdf.ln(10)

    pdf.set_draw_color(30, 60, 114)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    estado = orden_data.get("estado", "pendiente")
    color_estado = (39, 174, 96) if estado == "confirmado" else (230, 126, 34) if estado == "pendiente" else (200, 50, 50)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*color_estado)
    pdf.cell(0, 8, f"Estado: {estado.upper()}", align="R")
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 60, 114)
    pdf.cell(0, 6, "DATOS DEL PROVEEDOR", align="L")
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(50, 50, 50)
    proveedor = orden_data.get("proveedor", {})
    pdf.cell(0, 5, f"Proveedor: {        proveedor.get('nombre', '-')}")
    pdf.ln(5)
    pdf.cell(0, 5, f"Contacto: {proveedor.get('contacto', '-')}")
    pdf.ln(5)
    pdf.cell(0, 5, f"Telefono: {proveedor.get('telefono', '-')}")
    pdf.ln(5)
    pdf.cell(0, 5, f"Email: {proveedor.get('email', '-')}")
    pdf.ln(8)

    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 60, 114)
    pdf.cell(0, 6, "DETALLE DEL PEDIDO", align="L")
    pdf.ln(8)

    col_w = [30, 60, 25, 25, 25, 25]
    headers = ["Codigo", "Insumo", "Cantidad", "P. Unit.", "Subtotal", "F. Necesaria"]

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(30, 60, 114)
    pdf.set_text_color(255, 255, 255)
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 7, h, border=1, align="C", fill=True)
    pdf.ln()

    cantidad = orden_data.get("cantidad", 0)
    precio = orden_data.get("precio_unitario", 0)
    subtotal = cantidad * (precio if precio else 0)
    fecha_nec = orden_data.get("fecha_necesaria", "-")
    if hasattr(fecha_nec, 'strftime'):
        fecha_nec = fecha_nec.strftime("%d/%m/%Y")

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(50, 50, 50)
    pdf.set_fill_color(248, 249, 250)

    row_data = [
        str(orden_data.get("id", "-")),
        orden_data.get("insumo_nombre", orden_data.get("insumo", {}).get("nombre", "-")),
        f"{cantidad:.2f}",
        f"S/ {precio:.2f}" if precio else "-",
        f"S/ {subtotal:.2f}" if precio else "-",
        fecha_nec,
    ]
    for i, val in enumerate(row_data):
        val = sanitize(val)
        max_w = col_w[i] - 2
        while pdf.get_string_width(val) > max_w:
            val = val[:-1]
        pdf.cell(col_w[i], 6, val, border=1, align="C", fill=True)
    pdf.ln()

    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 9)
    if precio:
        pdf.set_text_color(30, 60, 114)
        pdf.cell(0, 6, f"Total: S/ {subtotal:.2f}", align="R")

    pdf.ln(10)

    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(0, 5, f"Fecha de orden: {orden_data.get('fecha_orden', '-')}", align="L")
    if hasattr(orden_data.get("fecha_orden"), "strftime"):
        pdf.cell(0, 5, f"Fecha de orden: {orden_data['fecha_orden'].strftime('%d/%m/%Y')}", align="L")
        pdf.ln(5)
    pdf.cell(0, 5, "Este documento es generado automaticamente por el Sistema Predictivo.", align="C")

    return bytes(pdf.output(dest="S"))


def generar_pdf_sugeridas(ordenes: list[dict]) -> bytes:
    pdf = OrdenPDF(orientation="L", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 60, 114)
    pdf.cell(0, 12, "ORDENES SUGERIDAS - PANADERIA VICTORIA", align="C")
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    hoy = date.today().strftime("%d/%m/%Y")
    pdf.cell(0, 6, f"Generado: {hoy}", align="C")
    pdf.ln(10)

    pdf.set_draw_color(30, 60, 114)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 287, pdf.get_y())
    pdf.ln(6)

    total_ordenes = len(ordenes)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(230, 126, 34)
    pdf.cell(0, 7, f"Total de ordenes sugeridas: {total_ordenes}", align="R")
    pdf.ln(10)

    col_w = [10, 40, 45, 25, 25, 35, 30, 30, 30]
    headers = ["#", "Proveedor", "Insumo", "Cantidad", "P. Unit.", "Subtotal", "Estado", "F. Orden", "F. Necesaria"]

    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(30, 60, 114)
    pdf.set_text_color(255, 255, 255)
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 7, h, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(50, 50, 50)
    total_general = 0

    for idx, ord in enumerate(ordenes):
        cantidad = ord.get("cantidad", 0)
        precio = ord.get("precio_unitario", 0)
        subtotal = cantidad * (precio if precio else 0)
        total_general += subtotal

        fecha_ord = ord.get("fecha_orden", "-")
        fecha_nec = ord.get("fecha_necesaria", "-")
        if hasattr(fecha_ord, 'strftime'):
            fecha_ord = fecha_ord.strftime("%d/%m/%Y")
        if hasattr(fecha_nec, 'strftime'):
            fecha_nec = fecha_nec.strftime("%d/%m/%Y")

        fill = idx % 2 == 0
        if fill:
            pdf.set_fill_color(248, 249, 250)

        row_data = [
            str(ord.get("id", idx + 1)),
            ord.get("proveedor_nombre", ord.get("proveedor", {}).get("nombre", "-")),
            ord.get("insumo_nombre", ord.get("insumo", {}).get("nombre", "-")),
            f"{cantidad:.2f}",
            f"S/ {precio:.2f}" if precio else "-",
            f"S/ {subtotal:.2f}" if precio else "-",
            ord.get("estado", "-"),
            fecha_ord,
            fecha_nec,
        ]
        for i, val in enumerate(row_data):
            val = sanitize(val)
            max_w = col_w[i] - 2
            while val and pdf.get_string_width(val) > max_w:
                val = val[:-1]
            pdf.cell(col_w[i], 5, val, border=1, align="C", fill=fill)

        pdf.ln()

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 60, 114)
    pdf.cell(0, 7, f"Total general: S/ {total_general:.2f}", align="R")

    pdf.ln(10)

    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(0, 5, "Este documento es generado automaticamente por el Sistema Predictivo.", align="C")

    return bytes(pdf.output(dest="S"))
