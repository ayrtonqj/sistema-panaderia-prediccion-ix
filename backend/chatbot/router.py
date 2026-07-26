"""
chatbot/router.py - Router de FastAPI para el chatbot de la panadería.
Proporciona respuestas básicas basadas en palabras clave sobre el sistema.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import date, timedelta
from typing import Optional
import sys
import os

# Importación relativa al paquete backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


class ChatMessage(BaseModel):
    mensaje: Optional[str] = None
    pregunta: Optional[str] = None
    username: str = ""


def get_db():
    from database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _respuesta_fallback(mensaje: str) -> str:
    msg = mensaje.lower()

    if any(w in msg for w in ["hola", "buenas", "saludos", "hi"]):
        return "¡Hola! Soy el asistente de Panadería Victoria. Puedo ayudarte con información sobre ventas, inventario, predicciones y mermas. ¿En qué te puedo ayudar?"

    if any(w in msg for w in ["venta", "vendido", "ingreso"]):
        return "Para ver las ventas del día o históricas, ve a la sección **Registro Diario** o **Dashboard**. También puedes consultar predicciones en la sección **Predicciones**."

    if any(w in msg for w in ["stock", "inventario", "insumo"]):
        return "El inventario de insumos está disponible en la sección **Inventario**. Puedes ver niveles de stock, alertas de reposición y registrar entradas."

    if any(w in msg for w in ["merma", "pérdida", "perdida", "desperdicio"]):
        return "Las mermas se registran en **Control de Pérdidas**. Puedes ver la tasa de merma y los productos con mayor desperdicio."

    if any(w in msg for w in ["prediccion", "predicción", "pronostico", "pronóstico"]):
        return "Las predicciones de demanda están en la sección **Predicciones**. Usa el modelo estadístico para anticipar cuánto producir cada día."

    if any(w in msg for w in ["proveedor", "compra", "orden"]):
        return "Gestiona proveedores en **Proveedores** y órdenes de compra en **Órdenes de Compra**. El sistema puede sugerir órdenes automáticamente."

    if any(w in msg for w in ["reporte", "informe", "excel", "pdf"]):
        return "Puedes generar reportes en la sección **Reportes Financieros**. Se exportan en PDF y Excel."

    if any(w in msg for w in ["ayuda", "help", "cómo", "como", "qué", "que"]):
        return ("Puedo orientarte sobre:\n"
                "• 📊 **Ventas** - Registro y consulta de ventas\n"
                "• 📦 **Inventario** - Stock de insumos\n"
                "• 🔮 **Predicciones** - Demanda futura\n"
                "• 📉 **Mermas** - Control de pérdidas\n"
                "• 🛒 **Órdenes de compra** - Gestión de proveedores\n"
                "• 📑 **Reportes** - Informes financieros\n\n"
                "¿Sobre cuál de estos temas quieres saber más?")

    return ("No entendí tu consulta. Puedes preguntarme sobre:\n"
            "ventas, inventario, predicciones, mermas, proveedores o reportes.")


@router.post("/mensaje")
@router.post("/pregunta")
def chatbot_mensaje(msg: ChatMessage, db: Session = Depends(get_db)):
    """Procesa un mensaje del chatbot y retorna una respuesta con datos reales de la BD."""
    texto_mensaje = msg.mensaje or msg.pregunta or ""
    try:
        import models
        from sqlalchemy import func

        mensaje_lower = texto_mensaje.lower()
        hoy = date.today()

        # 1. PREDICCIONES / PROYECCIONES DE PRODUCCIÓN
        if any(w in mensaje_lower for w in ["predicci", "proyecci", "pronost", "demanda", "cuánto producir", "cuanto producir", "lista por producto", "producción recomendada", "produccion recomendada"]):
            reciente = db.query(models.FactPrediccion.fecha_proyectada).order_by(models.FactPrediccion.fecha_proyectada.desc()).first()
            if reciente:
                fecha_target = reciente[0]
                preds = db.query(
                    models.DimProducto.nombre,
                    models.FactPrediccion.demanda_estimada,
                    models.FactPrediccion.algoritmo_utilizado
                ).join(
                    models.DimProducto, models.FactPrediccion.producto_id == models.DimProducto.id
                ).filter(
                    models.FactPrediccion.fecha_proyectada == fecha_target
                ).order_by(models.DimProducto.nombre).all()

                if preds:
                    lineas = [f"• {p.nombre}: **{round(float(p.demanda_estimada))} unidades**" for p in preds]
                    res = f"🔮 **Predicciones de Producción por Producto (Fecha: {fecha_target}):**\n\n" + "\n".join(lineas)
                    return {"respuesta": res, "mensaje": res}

        # 2. STOCK DE INSUMOS / INVENTARIO
        if any(w in mensaje_lower for w in ["stock", "inventario", "insumo", "reponer", "reabastecer", "ingrediente"]):
            insumos = db.query(models.InsumoCritico).order_by(models.InsumoCritico.nombre).all()
            if insumos:
                lineas = []
                for i in insumos:
                    alerta = "⚠️ (Bajo Stock)" if i.stock_actual <= i.stock_minimo else "✅"
                    lineas.append(f"• {i.nombre}: **{i.stock_actual} {i.unidad_medida}** (mín: {i.stock_minimo}) {alerta}")
                res = "📦 **Estado de Inventario e Insumos:**\n\n" + "\n".join(lineas)
                return {"respuesta": res, "mensaje": res}

        # 3. VENTAS / PRODUCTOS MÁS VENDIDOS
        if any(w in mensaje_lower for w in ["venta", "vendido", "ingreso", "más vendido", "mas vendido"]):
            top_ventas = db.query(
                models.DimProducto.nombre,
                func.sum(models.FactVenta.cantidad_vendida).label("cant_total"),
                func.sum(models.FactVenta.cantidad_vendida * models.DimProducto.precio).label("ingreso_total")
            ).join(
                models.DimProducto, models.FactVenta.producto_id == models.DimProducto.id
            ).group_by(models.DimProducto.nombre).order_by(text("cant_total DESC")).limit(10).all()

            if top_ventas:
                lineas = [f"• {tv.nombre}: **{int(tv.cant_total)} uds** (S/ {float(tv.ingreso_total or 0):.2f})" for tv in top_ventas]
                res = "📊 **Top Productos Más Vendidos:**\n\n" + "\n".join(lineas)
                return {"respuesta": res, "mensaje": res}

        # 4. MERMAS / PÉRDIDAS
        if any(w in mensaje_lower for w in ["merma", "pérdida", "perdida", "desperdicio"]):
            mermas = db.query(
                models.DimProducto.nombre,
                func.sum(models.FactMerma.cantidad_merma).label("cant_merma"),
                func.sum(models.FactMerma.cantidad_merma * models.DimProducto.costo).label("costo_merma")
            ).join(
                models.DimProducto, models.FactMerma.producto_id == models.DimProducto.id
            ).group_by(models.DimProducto.nombre).order_by(text("costo_merma DESC")).limit(8).all()

            if mermas:
                lineas = [f"• {m.nombre}: **{float(m.cant_merma):.1f} Kg/uds** (Pérdida est: S/ {float(m.costo_merma or 0):.2f})" for m in mermas]
                res = "📉 **Resumen de Mermas Registradas por Producto:**\n\n" + "\n".join(lineas)
                return {"respuesta": res, "mensaje": res}

        # 5. PROVEEDORES / ÓRDENES DE COMPRA
        if any(w in mensaje_lower for w in ["proveedor", "compra", "orden"]):
            ordenes = db.query(models.OrdenCompra).order_by(models.OrdenCompra.fecha_orden.desc()).limit(7).all()
            if ordenes:
                lineas = []
                for o in ordenes:
                    prov = o.proveedor.nombre if o.proveedor else "—"
                    insumo = o.insumo.nombre if o.insumo else "—"
                    lineas.append(f"• Orden #{o.id} ({o.fecha_orden}): **{insumo}** ({o.cantidad}) → {prov} [{o.estado.upper()}]")
                res = "🛒 **Órdenes de Compra Recientes:**\n\n" + "\n".join(lineas)
                return {"respuesta": res, "mensaje": res}

    except Exception as e:
        print(f"[CHATBOT ERR] {e}")

    respuesta = _respuesta_fallback(texto_mensaje)
    return {"respuesta": respuesta, "mensaje": respuesta}


@router.get("/estado")
def chatbot_estado():
    """Verifica que el chatbot esté operativo."""
    return {"estado": "ok", "version": "1.0"}
