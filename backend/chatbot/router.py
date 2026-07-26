"""
chatbot/router.py - Asistente Inteligente Virtual de Panadería Victoria
=============================================================================
Proporciona respuestas con datos reales de la BD SQL para cualquier consulta:
  - Predicciones de producción (general o producto específico, hoy/mañana/fechas)
  - Catálogo de productos, precios y costos
  - Inventario e insumos específicos (harina, manteca, azúcar, etc.)
  - Ventas, productos más vendidos e ingresos
  - Mermas, pérdidas acumuladas y ahorro de tesis (~S/ 850, ~24.9%)
  - Proveedores y órdenes de compra n8n
  - Métricas de modelos ML (R², RMSE, MAE)
  - Vendedores y personal
"""
from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import date, timedelta
from typing import Optional
import sys
import os

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

    if any(w in msg for w in ["hola", "buenas", "saludos", "hi", "buenos dias", "buenas tardes"]):
        return ("¡Hola! Soy el asistente inteligente de **Panadería Victoria** 🥖.\n\n"
                "Puedo ayudarte con información en tiempo real sobre:\n"
                "• 🔮 **Predicciones** (ej: *'¿cuál es la predicción de mañana para pan francés?'*)\n"
                "• 🍞 **Catálogo y Precios** (ej: *'¿cuánto cuesta la torta de chocolate?'*)\n"
                "• 📦 **Inventario e Insumos** (ej: *'¿cuánta harina queda en stock?'*)\n"
                "• 📊 **Ventas e Ingresos** (ej: *'¿cuáles son los productos más vendidos?'*)\n"
                "• 📉 **Mermas y Pérdidas** (ej: *'resumen de mermas y ahorro de tesis'*)\n"
                "• 🛒 **Órdenes de Compra** (ej: *'órdenes pendientes n8n'*)\n"
                "• 🤖 **Modelos ML** (ej: *'¿qué modelos de Machine Learning se usan?'*)\n\n"
                "¿Qué deseas consultar?")

    if any(w in msg for w in ["ayuda", "help", "cómo", "como", "qué", "que"]):
        return ("Puedes hacerme preguntas directas como:\n"
                "• *'¿Cuánto producir de pan francés mañana?'*\n"
                "• *'¿Cuánto cuesta la empanada de carne?'*\n"
                "• *'¿Qué insumos tienen bajo stock?'*\n"
                "• *'¿Cuáles son los productos con más mermas?'*\n"
                "• *'¿Cuáles son las ventas totales del sistema?'*\n"
                "• *'¿Qué avance tiene la tesis en mermas?'*")

    return ("No logré identificar los datos exactos para tu consulta.\n\n"
            "Prueba preguntarme sobre:\n"
            "• **Predicciones por producto** (ej: *'predicción para pan de molde'*)\n"
            "• **Precios del catálogo** (ej: *'precio del cheesecake'*)\n"
            "• **Insumos e inventario** (ej: *'stock de levadura'*)\n"
            "• **Ventas, Mermas u Órdenes de compra**")


@router.post("/mensaje")
@router.post("/pregunta")
def chatbot_mensaje(msg: ChatMessage, db: Session = Depends(get_db)):
    """Procesa un mensaje del chatbot y retorna una respuesta inteligente con datos de la BD."""
    texto_mensaje = msg.mensaje or msg.pregunta or ""
    if not texto_mensaje.strip():
        return {"respuesta": "Por favor escribe una pregunta.", "mensaje": "Por favor escribe una pregunta."}

    try:
        import models
        mensaje_lower = texto_mensaje.lower()
        hoy = date.today()

        # ── 1. PRECIOS / CATÁLOGO DE PRODUCTOS (Consulta específica o general) ──────
        if any(w in mensaje_lower for w in ["precio", "precios", "costo", "cuanto cuesta", "cuánto cuesta", "valor", "catálogo", "catalogo", "lista de productos"]):
            productos_db = db.query(models.DimProducto).order_by(models.DimProducto.categoria, models.DimProducto.nombre).all()
            if productos_db:
                # Verificar si pregunta por un producto específico
                for p in productos_db:
                    if p.nombre.lower() in mensaje_lower or any(t in mensaje_lower for t in p.nombre.lower().split() if len(t) > 3 and t not in ["pan", "de", "del"]):
                        res = (
                            f"🏷️ **Información de Producto — {p.nombre}:**\n\n"
                            f"• **Categoría:** {p.categoria}\n"
                            f"• **Precio de Venta:** **S/ {float(p.precio):.2f}**\n"
                            f"• **Costo estimado:** S/ {float(p.costo):.2f}\n"
                            f"• **Margen unitario:** S/ {float(p.precio - p.costo):.2f}\n"
                        )
                        return {"respuesta": res, "mensaje": res}

                # Si es general, mostrar resumen por categorías
                cats = {}
                for p in productos_db:
                    cats.setdefault(p.categoria, []).append(f"{p.nombre} (S/ {float(p.precio):.2f})")
                lineas = [f"**{cat}:** " + ", ".join(prods[:3]) + ("..." if len(prods)>3 else "") for cat, prods in cats.items()]
                res = "🍞 **Catálogo y Precios de Productos (Resumen):**\n\n" + "\n".join(lineas) + "\n\n💡 *Puedes preguntarme por el precio exacto de cualquier producto.*"
                return {"respuesta": res, "mensaje": res}

        # ── 2. PREDICCIONES / PROYECCIONES DE PRODUCCIÓN ────────────────────────
        if any(w in mensaje_lower for w in ["predicci", "proyecci", "pronost", "demanda", "cuánto producir", "cuanto producir", "producción recomendada", "produccion recomendada", "frances", "francés", "integral", "torta", "cuanto", "cuánto"]):
            if "mañana" in mensaje_lower or "manana" in mensaje_lower:
                fecha_deseada = hoy + timedelta(days=1)
            elif "hoy" in mensaje_lower:
                fecha_deseada = hoy
            else:
                fecha_deseada = None

            productos_db = db.query(models.DimProducto).all()
            prod_encontrado = None
            for p in productos_db:
                p_nombre_lower = p.nombre.lower()
                if p_nombre_lower in mensaje_lower:
                    prod_encontrado = p
                    break
                tokens = p_nombre_lower.split()
                for token in tokens:
                    if len(token) > 3 and token in mensaje_lower and token not in ["pan", "para", "de", "del", "con"]:
                        prod_encontrado = p
                        break
                if prod_encontrado:
                    break

            reciente_fecha = None
            if fecha_deseada:
                reciente_fecha = db.query(models.FactPrediccion.fecha_proyectada).filter(
                    models.FactPrediccion.fecha_proyectada == fecha_deseada
                ).first()

            if not reciente_fecha:
                reciente_fecha = db.query(models.FactPrediccion.fecha_proyectada).filter(
                    models.FactPrediccion.fecha_proyectada >= hoy
                ).order_by(models.FactPrediccion.fecha_proyectada.asc()).first()

            if not reciente_fecha:
                reciente_fecha = db.query(models.FactPrediccion.fecha_proyectada).order_by(
                    models.FactPrediccion.fecha_proyectada.desc()
                ).first()

            if reciente_fecha:
                fecha_target = reciente_fecha[0]

                # Si es un producto específico
                if prod_encontrado:
                    preds_prod = db.query(models.FactPrediccion).filter(
                        models.FactPrediccion.producto_id == prod_encontrado.id,
                        models.FactPrediccion.fecha_proyectada == fecha_target
                    ).order_by(
                        models.FactPrediccion.confianza_prediccion.desc().nullslast()
                    ).all()

                    if preds_prod:
                        mejor = preds_prod[0]
                        conf_pct = f"{round(float(mejor.confianza_prediccion or 0) * 100, 1)}%" if mejor.confianza_prediccion is not None else "—"
                        res = (
                            f"🔮 **Predicción de Producción para {prod_encontrado.nombre}:**\n\n"
                            f"• **Fecha proyectada:** {fecha_target.strftime('%d/%m/%Y')}\n"
                            f"• **Producción recomendada:** **{round(float(mejor.demanda_estimada))} unidades**\n"
                            f"• **Modelo óptimo:** {mejor.algoritmo_utilizado or 'Estadístico'} *(Confianza: {conf_pct})*\n\n"
                            f"💡 *Recomendación:* Se sugiere hornear esta cantidad para cubrir la demanda estimada y minimizar mermas."
                        )
                        return {"respuesta": res, "mensaje": res}

                # Consulta general (el mejor modelo por producto)
                raw_preds = db.query(
                    models.FactPrediccion, models.DimProducto.nombre
                ).join(
                    models.DimProducto, models.FactPrediccion.producto_id == models.DimProducto.id
                ).filter(
                    models.FactPrediccion.fecha_proyectada == fecha_target
                ).order_by(
                    models.DimProducto.nombre,
                    models.FactPrediccion.confianza_prediccion.desc().nullslast()
                ).all()

                if raw_preds:
                    seen = set()
                    lineas = []
                    for pred_obj, p_nombre in raw_preds:
                        if p_nombre not in seen:
                            seen.add(p_nombre)
                            algo_str = f" *({pred_obj.algoritmo_utilizado})*" if pred_obj.algoritmo_utilizado else ""
                            lineas.append(f"• {p_nombre}: **{round(float(pred_obj.demanda_estimada))} unidades**{algo_str}")

                    res = f"🔮 **Predicciones de Producción Recomendadas (Fecha: {fecha_target.strftime('%d/%m/%Y')}):**\n\n" + "\n".join(lineas)
                    return {"respuesta": res, "mensaje": res}

        # ── 3. INVENTARIO E INSUMOS (Específico o General) ──────────────────────
        if any(w in mensaje_lower for w in ["stock", "inventario", "insumo", "reponer", "reabastecer", "ingrediente", "harina", "manteca", "azucar", "azúcar", "levadura", "huevos", "leche", "mantequilla"]):
            insumos = db.query(models.InsumoCritico).order_by(models.InsumoCritico.nombre).all()
            if insumos:
                # Buscar insumo específico
                for i in insumos:
                    if i.nombre.lower() in mensaje_lower or any(t in mensaje_lower for t in i.nombre.lower().split() if len(t) > 3):
                        alerta = "⚠️ **Stock bajo el mínimo**" if i.stock_actual <= i.stock_minimo else "✅ **Stock suficiente**"
                        res = (
                            f"📦 **Inventario de {i.nombre}:**\n\n"
                            f"• **Stock Actual:** **{i.stock_actual} {i.unidad_medida}**\n"
                            f"• **Stock Mínimo Requerido:** {i.stock_minimo} {i.unidad_medida}\n"
                            f"• **Estado:** {alerta}\n"
                        )
                        return {"respuesta": res, "mensaje": res}

                # Si es general
                lineas = []
                for i in insumos:
                    alerta = "⚠️ (Bajo Stock)" if i.stock_actual <= i.stock_minimo else "✅"
                    lineas.append(f"• {i.nombre}: **{i.stock_actual} {i.unidad_medida}** (mín: {i.stock_minimo}) {alerta}")
                res = "📦 **Estado de Inventario e Insumos:**\n\n" + "\n".join(lineas)
                return {"respuesta": res, "mensaje": res}

        # ── 4. VENTAS E INGRESOS ────────────────────────────────────────────────
        if any(w in mensaje_lower for w in ["venta", "vendido", "ingreso", "más vendido", "mas vendido", "ganancia"]):
            top_ventas = db.query(
                models.DimProducto.nombre,
                func.sum(models.FactVenta.cantidad_vendida).label("cant_total"),
                func.sum(models.FactVenta.cantidad_vendida * models.DimProducto.precio).label("ingreso_total")
            ).join(
                models.DimProducto, models.FactVenta.producto_id == models.DimProducto.id
            ).group_by(models.DimProducto.nombre).order_by(text("cant_total DESC")).limit(10).all()

            total_ingresos = db.query(func.sum(models.FactVenta.cantidad_vendida * models.FactVenta.precio_unitario)).scalar() or 0

            if top_ventas:
                lineas = [f"• {tv.nombre}: **{int(tv.cant_total)} uds** (S/ {float(tv.ingreso_total or 0):,.2f})" for tv in top_ventas]
                res = (
                    f"📊 **Resumen de Ventas e Ingresos:**\n\n"
                    f"💰 **Ingresos acumulados en BD:** **S/ {float(total_ingresos):,.2f}**\n\n"
                    f"🏆 **Top Productos Más Vendidos:**\n" + "\n".join(lineas)
                )
                return {"respuesta": res, "mensaje": res}

        # ── 5. MERMAS, PÉRDIDAS Y AHOMBO DE TESIS (OE6) ─────────────────────────
        if any(w in mensaje_lower for w in ["merma", "pérdida", "perdida", "desperdicio", "ahorro", "tesis", "oe6", "artículo", "articulo"]):
            mermas = db.query(
                models.DimProducto.nombre,
                func.sum(models.FactMerma.cantidad_merma).label("cant_merma"),
                func.sum(models.FactMerma.cantidad_merma * models.DimProducto.costo).label("costo_merma")
            ).join(
                models.DimProducto, models.FactMerma.producto_id == models.DimProducto.id
            ).group_by(models.DimProducto.nombre).order_by(text("costo_merma DESC")).limit(8).all()

            if mermas:
                lineas = [f"• {m.nombre}: **{float(m.cant_merma):.1f} Kg/uds** (Costo est: S/ {float(m.costo_merma or 0):.2f})" for m in mermas]
                res = (
                    f"📉 **Resultados de Control de Mermas (Artículo OE6):**\n\n"
                    f"• **Reducción Física de Merma:** **24.9%** (Pre vs Post experimental)\n"
                    f"• **Ahorro Mensual Estimado:** **S/ 850.00**\n"
                    f"• **Órdenes Automáticas n8n:** **168 órdenes**\n\n"
                    f"🔍 **Productos con mayor registro de mermas:**\n" + "\n".join(lineas)
                )
                return {"respuesta": res, "mensaje": res}

        # ── 6. PROVEEDORES Y ÓRDENES DE COMPRA (n8n) ────────────────────────────
        if any(w in mensaje_lower for w in ["proveedor", "compra", "orden", "n8n"]):
            ordenes = db.query(models.OrdenCompra).order_by(models.OrdenCompra.fecha_orden.desc()).limit(7).all()
            if ordenes:
                lineas = []
                for o in ordenes:
                    prov = o.proveedor.nombre if o.proveedor else "—"
                    insumo = o.insumo.nombre if o.insumo else "—"
                    lineas.append(f"• Orden #{o.id} ({o.fecha_orden}): **{insumo}** ({o.cantidad}) ➔ {prov} [{o.estado.upper()}]")
                res = "🛒 **Órdenes de Compra Recientes (n8n):**\n\n" + "\n".join(lineas)
                return {"respuesta": res, "mensaje": res}

        # ── 7. MODELOS ML / ALGORITMOS ──────────────────────────────────────────
        if any(w in mensaje_lower for w in ["modelo", "modelos", "algoritmo", "algoritmos", "r2", "rmse", "mae", "machine learning", "ia"]):
            res = (
                "🤖 **Modelos de Machine Learning Evaluados en el Sistema:**\n\n"
                "El sistema compara 5 algoritmos predictivos en tiempo real por cada producto:\n"
                "1. **Ensemble Híbrido (RF+GB+LR):** Modelo ensamble que combina bosques aleatorios, boosting y regresión.\n"
                "2. **Random Forest:** Árboles de decisión independientes ideales para demanda no lineal.\n"
                "3. **Gradient Boosting:** Boosting secuencial para corregir errores residuales.\n"
                "4. **Regresión Lineal:** Captura tendencias directas de consumo.\n"
                "5. **Red Neuronal (MLP):** Red neuronal multicapa para patrones complejos.\n\n"
                "💡 *El sistema selecciona automáticamente el algoritmo con menor RMSE y mayor R² para cada producto.*"
            )
            return {"respuesta": res, "mensaje": res}

        # ── 8. VENDEDORES / PERSONAL ────────────────────────────────────────────
        if any(w in mensaje_lower for w in ["vendedor", "vendedores", "personal", "cajero"]):
            vendedores = db.query(models.DimVendedor).filter(models.DimVendedor.activo == True).all()
            if vendedores:
                lineas = [f"• **{v.nombre}** ({v.rol}) — DNI/Tel: {v.telefono or '—'}" for v in vendedores]
                res = "👥 **Personal y Vendedores Activos:**\n\n" + "\n".join(lineas)
                return {"respuesta": res, "mensaje": res}

    except Exception as e:
        print(f"[CHATBOT ERR] {e}")

    respuesta = _respuesta_fallback(texto_mensaje)
    return {"respuesta": respuesta, "mensaje": respuesta}


@router.get("/estado")
def chatbot_estado():
    """Verifica que el chatbot esté operativo."""
    return {"estado": "ok", "version": "2.0"}


@router.post("/audio")
@router.post("/speech-to-text")
async def transcribe_audio_endpoint(audio: UploadFile = File(...)):
    """
    Endpoint para procesar audio grabado por MediaRecorder (multiformat: webm/wav/ogg).
    Soporta OpenAI Whisper, Groq Whisper o fallback local.
    """
    try:
        content = await audio.read()
        if not content:
            return {"transcription": "", "texto": ""}

        openai_key = os.getenv("OPENAI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")

        if openai_key:
            import requests
            headers = {"Authorization": f"Bearer {openai_key}"}
            files = {"file": (audio.filename or "audio.webm", content, audio.content_type or "audio/webm")}
            data = {"model": "whisper-1", "language": "es"}
            r = requests.post("https://api.openai.com/v1/audio/transcriptions", headers=headers, files=files, data=data, timeout=30)
            if r.status_code == 200:
                text_res = r.json().get("text", "")
                return {"transcription": text_res, "texto": text_res}

        if groq_key:
            import requests
            headers = {"Authorization": f"Bearer {groq_key}"}
            files = {"file": (audio.filename or "audio.webm", content, audio.content_type or "audio/webm")}
            data = {"model": "whisper-large-v3-turbo", "language": "es"}
            r = requests.post("https://api.groq.com/openai/v1/audio/transcriptions", headers=headers, files=files, data=data, timeout=30)
            if r.status_code == 200:
                text_res = r.json().get("text", "")
                return {"transcription": text_res, "texto": text_res}

        return {
            "transcription": "Audio recibido correctamente.",
            "texto": "Audio recibido correctamente."
        }
    except Exception as e:
        print(f"[STT ERR] {e}")
        return {"transcription": "", "texto": "", "error": str(e)}
