"""
seed_data.py — Generador de datos históricos sintéticos realistas
Genera 365 días de ventas, mermas y clima para la Panadería Victoria.
Patrones modelados:
  - Estacionalidad semanal: fines de semana +35%, lunes bajo
  - Feriados peruanos: +50% en feriados nacionales
  - Verano peruano (Dic-Mar): +15% por temperatura
  - Mermas proporcionales a sobreproducción (buffer del 10-20%)
  - Clima con variación estacional realista para Pacasmayo (costa norte Perú)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import random
import numpy as np
from datetime import date, timedelta
from database import SessionLocal
import models

# Semilla para reproducibilidad
random.seed(42)
np.random.seed(42)

# ── Feriados peruanos 2024-2025 ──────────────────────────────────────────────
FERIADOS_PERU = {
    date(2024, 1, 1), date(2024, 4, 18), date(2024, 4, 19),
    date(2024, 5, 1), date(2024, 6, 7), date(2024, 6, 29),
    date(2024, 7, 28), date(2024, 7, 29), date(2024, 8, 30),
    date(2024, 10, 8), date(2024, 11, 1), date(2024, 12, 8),
    date(2024, 12, 25),
    date(2025, 1, 1), date(2025, 4, 17), date(2025, 4, 18),
    date(2025, 5, 1), date(2025, 6, 7), date(2025, 6, 29),
}

# Eventos especiales locales (Pacasmayo)
EVENTOS_ESPECIALES = {
    date(2024, 5, 12): "Día de la Madre",
    date(2024, 6, 16): "Día del Padre",
    date(2024, 7, 28): "Fiestas Patrias",
    date(2024, 12, 24): "Nochebuena",
    date(2025, 2, 14): "San Valentín",
}

# ── Productos de una panadería real ─────────────────────────────────────────
PRODUCTOS = [
    # Pan de mesa (4)
    {"nombre": "Pan Frances",       "categoria": "Pan de mesa",  "precio": 0.20, "costo": 0.10, "base_dia": 200},
    {"nombre": "Pan Integral",      "categoria": "Pan de mesa",  "precio": 0.30, "costo": 0.15, "base_dia": 80},
    {"nombre": "Pan de Chicharrón", "categoria": "Pan de mesa",  "precio": 0.50, "costo": 0.25, "base_dia": 40},
    {"nombre": "Pan de Yema",       "categoria": "Pan de mesa",  "precio": 0.30, "costo": 0.15, "base_dia": 60},
    # Pan especial (4)
    {"nombre": "Pan de Molde",      "categoria": "Pan especial", "precio": 5.00, "costo": 2.50, "base_dia": 15},
    {"nombre": "Pan Ciabatta",      "categoria": "Pan especial", "precio": 4.00, "costo": 2.00, "base_dia": 12},
    {"nombre": "Pan Baguette",      "categoria": "Pan especial", "precio": 3.50, "costo": 1.75, "base_dia": 20},
    {"nombre": "Pan de Centeno",    "categoria": "Pan especial", "precio": 6.00, "costo": 3.00, "base_dia": 8},
    # Bollería (4)
    {"nombre": "Croissant",         "categoria": "Bollería",     "precio": 2.50, "costo": 1.20, "base_dia": 30},
    {"nombre": "Dona Glaseada",     "categoria": "Bollería",     "precio": 2.00, "costo": 1.00, "base_dia": 25},
    {"nombre": "Alfajor",           "categoria": "Bollería",     "precio": 1.50, "costo": 0.75, "base_dia": 40},
    {"nombre": "Empanada de Manzana","categoria": "Bollería",    "precio": 2.00, "costo": 1.00, "base_dia": 20},
    # Salados (4)
    {"nombre": "Empanada de Carne", "categoria": "Salados",      "precio": 1.50, "costo": 0.70, "base_dia": 50},
    {"nombre": "Empanada de Pollo", "categoria": "Salados",      "precio": 2.00, "costo": 1.00, "base_dia": 35},
    {"nombre": "Pan con Chicharrón","categoria": "Salados",      "precio": 3.00, "costo": 1.50, "base_dia": 25},
    {"nombre": "Empanada de Queso", "categoria": "Salados",      "precio": 1.80, "costo": 0.90, "base_dia": 30},
    # Pasteles (4)
    {"nombre": "Torta de Cumpleaños","categoria": "Pasteles",    "precio": 50.0, "costo": 25.0, "base_dia": 2},
    {"nombre": "Cheesecake",        "categoria": "Pasteles",     "precio": 35.0, "costo": 17.5, "base_dia": 3},
    {"nombre": "Pie de Limón",      "categoria": "Pasteles",     "precio": 25.0, "costo": 12.5, "base_dia": 4},
    {"nombre": "Torta de Chocolate", "categoria": "Pasteles",    "precio": 40.0, "costo": 20.0, "base_dia": 3},
    # Dulces (4)
    {"nombre": "Galletas de Avena", "categoria": "Dulces",       "precio": 0.50, "costo": 0.20, "base_dia": 60},
    {"nombre": "Bizcocho",          "categoria": "Dulces",       "precio": 0.80, "costo": 0.40, "base_dia": 40},
    {"nombre": "Suspiro Limeño",    "categoria": "Dulces",       "precio": 3.00, "costo": 1.50, "base_dia": 15},
    {"nombre": "Arroz con Leche",   "categoria": "Dulces",       "precio": 2.00, "costo": 1.00, "base_dia": 20},
]

# ── Insumos críticos ─────────────────────────────────────────────────────────
INSUMOS = [
    {"nombre": "Harina de Trigo",  "stock_actual": 200, "stock_minimo": 50, "unidad_medida": "Kg"},
    {"nombre": "Azúcar",           "stock_actual": 80,  "stock_minimo": 20, "unidad_medida": "Kg"},
    {"nombre": "Mantequilla",      "stock_actual": 30,  "stock_minimo": 10, "unidad_medida": "Kg"},
    {"nombre": "Levadura",         "stock_actual": 5,   "stock_minimo": 2,  "unidad_medida": "Kg"},
    {"nombre": "Huevos",           "stock_actual": 300, "stock_minimo": 60, "unidad_medida": "Unidades"},
    {"nombre": "Leche",            "stock_actual": 50,  "stock_minimo": 15, "unidad_medida": "Litros"},
    {"nombre": "Sal",              "stock_actual": 25,  "stock_minimo": 5,  "unidad_medida": "Kg"},
]

# ── Proveedores ──────────────────────────────────────────────────────────────
PROVEEDORES = [
    {"nombre": "Molinos del Norte SAC", "contacto": "Juan Pérez",   "telefono": "044-123456", "email": "ventas@molinosnorte.com"},
    {"nombre": "Distribuidora Lácteos La Victoria", "contacto": "María García", "telefono": "044-654321", "email": "pedidos@lacteoslavictoria.com"},
    {"nombre": "Agropecuaria Los Andes", "contacto": "Carlos Ruiz",  "telefono": "044-111222", "email": "carlos@losandes.pe"},
]

# ── Recetas (fichas técnicas) ────────────────────────────────────────────────
# producto_idx → [(insumo_idx, cantidad_por_unidad)]
RECETAS = {
    0:  [(0, 0.100), (3, 0.002), (6, 0.005)],    # Pan Frances (Pan de mesa)
    1:  [(0, 0.090), (3, 0.002), (6, 0.005)],    # Pan Integral
    2:  [(0, 0.100), (3, 0.002), (6, 0.005)],    # Pan de Chicharrón
    3:  [(0, 0.090), (4, 0.500), (1, 0.010), (3, 0.002)],  # Pan de Yema
    4:  [(0, 0.200), (1, 0.050), (5, 0.100)],    # Pan de Molde (Pan especial)
    5:  [(0, 0.150), (3, 0.003), (6, 0.008), (5, 0.050)],  # Pan Ciabatta
    6:  [(0, 0.180), (3, 0.003), (6, 0.007)],    # Pan Baguette
    7:  [(0, 0.120), (3, 0.002), (6, 0.005)],    # Pan de Centeno
    8:  [(0, 0.080), (2, 0.030), (4, 1.000)],    # Croissant (Bollería)
    9:  [(0, 0.060), (1, 0.040), (2, 0.020), (4, 0.500)],  # Dona Glaseada
    10: [(0, 0.040), (1, 0.030), (2, 0.020)],    # Alfajor
    11: [(0, 0.080), (1, 0.020), (2, 0.010), (4, 0.300)],  # Empanada de Manzana
    12: [(0, 0.120), (2, 0.010), (4, 0.500)],    # Empanada de Carne (Salados)
    13: [(0, 0.120), (2, 0.010), (4, 0.500)],    # Empanada de Pollo
    14: [(0, 0.100), (3, 0.002), (6, 0.005)],    # Pan con Chicharrón
    15: [(0, 0.100), (2, 0.015), (4, 0.300)],    # Empanada de Queso
    16: [(0, 0.500), (1, 0.300), (2, 0.200), (4, 6.0)],  # Torta de Cumpleaños (Pasteles)
    17: [(2, 0.150), (1, 0.100), (4, 3.000), (5, 0.200)], # Cheesecake
    18: [(0, 0.100), (2, 0.080), (1, 0.150), (4, 2.000), (5, 0.150)],  # Pie de Limón
    19: [(0, 0.350), (1, 0.250), (2, 0.150), (4, 4.000), (5, 0.100)],  # Torta de Chocolate
    20: [(0, 0.050), (1, 0.030), (2, 0.010)],    # Galletas de Avena (Dulces)
    21: [(0, 0.060), (1, 0.040), (4, 0.800), (2, 0.020)],  # Bizcocho
    22: [(5, 0.100), (1, 0.080), (4, 1.000)],    # Suspiro Limeño
    23: [(5, 0.150), (1, 0.050)],                 # Arroz con Leche
}

MOTIVOS_MERMA = [
    "Sobreproducción",
    "Caducidad",
    "Daño en manipulación",
    "Falla en cocción",
    "Devolución cliente",
]


def factor_dia(fecha: date) -> float:
    """Calcula el multiplicador de ventas para una fecha dada."""
    dow = fecha.weekday()  # 0=Lunes, 6=Domingo
    factor = 1.0

    # Estacionalidad semanal
    factores_semana = {0: 0.70, 1: 0.75, 2: 0.80, 3: 0.85, 4: 1.00, 5: 1.35, 6: 1.30}
    factor *= factores_semana.get(dow, 1.0)

    # Feriados y eventos
    if fecha in FERIADOS_PERU:
        factor *= 1.50
    if fecha in EVENTOS_ESPECIALES:
        factor *= 1.40

    # Verano costero peruano (Dic-Mar): más calor, más consumo de pan fresco
    if fecha.month in [12, 1, 2, 3]:
        factor *= 1.15

    return factor


def clima_dia(fecha: date) -> dict:
    """Genera datos climáticos realistas para Pacasmayo (costa norte, ~18-27°C)."""
    mes = fecha.month
    # Temperatura por mes (costa norte peruana)
    temp_base = {1: 26, 2: 27, 3: 26, 4: 24, 5: 22, 6: 19,
                 7: 18, 8: 18, 9: 19, 10: 20, 11: 22, 12: 24}[mes]
    temperatura = round(temp_base + np.random.normal(0, 1.5), 1)

    # Condición climática (costa norte raramente llueve)
    probs = [0.65, 0.20, 0.10, 0.04, 0.01]
    condicion = np.random.choice(
        ["Soleado", "Parcialmente nublado", "Nublado", "Lluvia ligera", "Lluvia"],
        p=probs
    )

    return {
        "fecha": fecha,
        "temperatura_promedio": temperatura,
        "condicion": condicion,
        "es_feriado": fecha in FERIADOS_PERU,
        "evento_especial": EVENTOS_ESPECIALES.get(fecha),
    }


def run_seed():
    db = SessionLocal()
    try:
        # Verificar si ya hay datos
        if db.query(models.DimProducto).count() > 0:
            print("[AVISO] Ya existen datos en la BD. Omitiendo seed para no duplicar.")
            return {"status": "omitido", "mensaje": "La BD ya tiene datos"}

        print("[SEED] Iniciando seed de datos historicos...")

        # ── 1. Proveedores ─────────────────────────────────────────────────
        print("  -> Insertando proveedores...")
        proveedores_db = []
        for p in PROVEEDORES:
            prov = models.Proveedor(**p)
            db.add(prov)
            proveedores_db.append(prov)
        db.flush()

        # ── 2. Productos ──────────────────────────────────────────────────
        print("  -> Insertando productos...")
        productos_db = []
        for p in PRODUCTOS:
            prod = models.DimProducto(
                nombre=p["nombre"],
                categoria=p["categoria"],
                precio=p["precio"],
                costo=p["costo"],
            )
            db.add(prod)
            productos_db.append(prod)
        db.flush()

        # ── 3. Insumos ────────────────────────────────────────────────────
        print("  -> Insertando insumos criticos...")
        insumos_db = []
        for i, ins in enumerate(INSUMOS):
            # Asignar proveedor principal según tipo de insumo
            prov_id = proveedores_db[0].id  # Molinos del Norte para harina
            if i in [1, 2, 5]:  # azúcar, mantequilla, leche → lácteos
                prov_id = proveedores_db[1].id
            if i in [4]:  # huevos → agropecuaria
                prov_id = proveedores_db[2].id

            insumo = models.InsumoCritico(
                nombre=ins["nombre"],
                stock_actual=ins["stock_actual"],
                stock_minimo=ins["stock_minimo"],
                unidad_medida=ins["unidad_medida"],
                proveedor_id=prov_id,
            )
            db.add(insumo)
            insumos_db.append(insumo)
        db.flush()

        # ── 4. Fichas técnicas (recetas) ──────────────────────────────────
        print("  -> Insertando fichas tecnicas (recetas)...")
        for prod_idx, ingredientes in RECETAS.items():
            for insumo_idx, cantidad in ingredientes:
                ficha = models.FichaTecnica(
                    producto_id=productos_db[prod_idx].id,
                    insumo_id=insumos_db[insumo_idx].id,
                    cantidad_necesaria=cantidad,
                )
                db.add(ficha)

        # ── 5. Datos históricos (365 días + 15 días de futuro para clima) ──
        fecha_inicio = date.today() - timedelta(days=365)
        fecha_fin_datos = date.today()
        fecha_fin_clima = date.today() + timedelta(days=15)
        delta = timedelta(days=1)

        ventas_total = 0
        mermas_total = 0
        clima_total = 0

        print(f"  -> Generando datos ({fecha_inicio} -> {fecha_fin_clima})...")

        fecha = fecha_inicio
        while fecha <= fecha_fin_clima:
            # Clima siempre se genera (pasado y futuro)
            clima = clima_dia(fecha)
            db_clima = models.DimClima(**clima)
            db.add(db_clima)
            clima_total += 1

            # Ventas solo hasta hoy (pasado)
            if fecha <= fecha_fin_datos:
                factor = factor_dia(fecha)
                for i, prod in enumerate(productos_db):
                    prod_info = PRODUCTOS[i]
                    base = prod_info["base_dia"]
                    vendida = max(0, round(base * factor * (1 + np.random.normal(0, 0.15))))
                    buffer_pct = np.random.uniform(0.10, 0.25)
                    producida = round(vendida * (1 + buffer_pct))

                    db.add(models.FactVenta(
                        producto_id=prod.id,
                        fecha=fecha,
                        cantidad_vendida=float(vendida),
                    ))
                    ventas_total += 1

                    db.add(models.FactProduccion(
                        producto_id=prod.id,
                        fecha=fecha,
                        cantidad_producida=float(producida),
                    ))

                    merma_real = producida - vendida
                    if merma_real > 0:
                        motivo = random.choices(
                            MOTIVOS_MERMA,
                            weights=[0.60, 0.20, 0.10, 0.07, 0.03]
                        )[0]
                        db.add(models.FactMerma(
                            producto_id=prod.id,
                            fecha=fecha,
                            cantidad_merma=float(merma_real),
                            motivo=motivo,
                        ))
                        mermas_total += 1

            fecha += delta

        db.commit()

        resumen = {
            "status": "ok",
            "productos": len(productos_db),
            "insumos": len(insumos_db),
            "proveedores": len(proveedores_db),
            "registros_ventas": ventas_total,
            "registros_mermas": mermas_total,
            "registros_clima": clima_total,
        }
        print(f"  [OK] Seed completado: {resumen}")
        return resumen

    except Exception as e:
        db.rollback()
        print(f"  [ERROR] Error en seed: {e}")
        raise e
    finally:
        db.close()


BASE_DIA_POR_CATEGORIA = {
    "Pan de mesa": 50,
    "Pan especial": 12,
    "Bollería": 25,
    "Salados": 30,
    "Pasteles": 3,
    "Dulces": 20,
}


def completar_datos_faltantes():
    """
    Genera datos sinteticos (ventas, produccion, mermas) para productos
    que tienen menos de 30 registros. También se asegura que existan
    datos climáticos para los últimos 365 días.
    """
    db = SessionLocal()
    try:
        productos = db.query(models.DimProducto).all()
        hoy = date.today()
        hace_365 = hoy - timedelta(days=365)

        productos_completados = 0

        for prod in productos:
            count = db.query(models.FactVenta).filter(
                models.FactVenta.producto_id == prod.id
            ).count()

            if count >= 30:
                continue

            categoria = (prod.categoria or "").strip()
            base_dia = BASE_DIA_POR_CATEGORIA.get(categoria, 15)

            print(f"  -> Generando datos para: {prod.nombre} (cat={categoria}, base={base_dia})")

            fecha = hace_365
            while fecha <= hoy:
                # Clima si no existe
                clima_existente = db.query(models.DimClima).filter(
                    models.DimClima.fecha == fecha
                ).first()
                if not clima_existente:
                    clima = clima_dia(fecha)
                    db.add(models.DimClima(**clima))

                # Ventas
                factor = factor_dia(fecha)
                vendida = max(0, round(base_dia * factor * (1 + np.random.normal(0, 0.15))))
                db.add(models.FactVenta(
                    producto_id=prod.id,
                    fecha=fecha,
                    cantidad_vendida=float(vendida),
                ))

                # Producción
                buffer_pct = np.random.uniform(0.10, 0.25)
                producida = round(vendida * (1 + buffer_pct))
                db.add(models.FactProduccion(
                    producto_id=prod.id,
                    fecha=fecha,
                    cantidad_producida=float(producida),
                ))

                # Merma
                merma_real = producida - vendida
                if merma_real > 0:
                    motivo = random.choices(
                        MOTIVOS_MERMA,
                        weights=[0.60, 0.20, 0.10, 0.07, 0.03]
                    )[0]
                    db.add(models.FactMerma(
                        producto_id=prod.id,
                        fecha=fecha,
                        cantidad_merma=float(merma_real),
                        motivo=motivo,
                    ))

                fecha += timedelta(days=1)

            productos_completados += 1

        db.commit()
        msg = f"Datos generados para {productos_completados} productos"
        print(f"  [OK] {msg}")
        return {"status": "ok", "productos_completados": productos_completados, "mensaje": msg}

    except Exception as e:
        db.rollback()
        print(f"  [ERROR] Error completando datos: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
