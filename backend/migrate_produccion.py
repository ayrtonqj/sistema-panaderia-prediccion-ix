"""
Migración: separa cantidad_producida de fact_ventas → fact_produccion.

Usa SQL directo porque la columna cantidad_producida ya no existe
en el modelo FactVenta (se eliminó), pero aún persiste en la BD.

1. Lee filas de fact_ventas con cantidad_producida IS NOT NULL
2. Crea registros en fact_produccion
3. Si producido > vendido, verifica/crea merma de Sobreproducción
"""
from database import SessionLocal
from sqlalchemy import text

def columna_existe(db, tabla, columna):
    """Verifica si una columna existe en la BD (consultando INFORMATION_SCHEMA)."""
    try:
        db.execute(text(f"SELECT \"{columna}\" FROM \"{tabla}\" WHERE 1=0"))
        return True
    except Exception:
        return False

def run_migracion():
    db = SessionLocal()
    try:
        # Verificar si la columna vieja aún existe
        if not columna_existe(db, "fact_ventas", "cantidad_producida"):
            print("[MIGRACION] La columna 'cantidad_producida' ya no existe en fact_ventas. Nada que migrar.")
            return {"status": "ok", "mensaje": "columna ya migrada o eliminada"}

        # Contar filas con producción
        n_producidas = db.execute(text(
            "SELECT COUNT(*) FROM fact_ventas WHERE cantidad_producida IS NOT NULL AND cantidad_producida > 0"
        )).scalar() or 0

        if n_producidas == 0:
            print("[MIGRACION] No hay datos con cantidad_producida en fact_ventas. Nada que migrar.")
            return {"status": "ok", "migrados": 0}

        print(f"[MIGRACION] Migrando {n_producidas} registros de producción...")

        # Obtener los datos viejos
        filas = db.execute(text(
            "SELECT id, producto_id, fecha, cantidad_vendida, cantidad_producida FROM fact_ventas WHERE cantidad_producida IS NOT NULL AND cantidad_producida > 0 ORDER BY fecha ASC"
        )).all()

        creados = 0
        mermas_creadas = 0
        for v in filas:
            prod_id, fecha, vendida, producida = v.producto_id, v.fecha, v.cantidad_vendida, v.cantidad_producida

            # Verificar si ya existe producción para ese producto/fecha
            existente = db.execute(text(
                "SELECT id FROM fact_produccion WHERE producto_id = :pid AND fecha = :f"
            ), {"pid": prod_id, "f": fecha}).first()
            if existente:
                continue

            db.execute(text(
                "INSERT INTO fact_produccion (producto_id, fecha, cantidad_producida) VALUES (:pid, :f, :cant)"
            ), {"pid": prod_id, "f": fecha, "cant": float(producida)})
            creados += 1

            # Si producido > vendido y no existe merma de sobreproducción, crearla
            if producida > vendida:
                excedente = round(producida - vendida, 2)
                merma_existente = db.execute(text(
                    "SELECT id FROM fact_mermas WHERE producto_id = :pid AND fecha = :f AND motivo = 'Sobreproducción'"
                ), {"pid": prod_id, "f": fecha}).first()
                if not merma_existente:
                    db.execute(text(
                        "INSERT INTO fact_mermas (producto_id, fecha, cantidad_merma, motivo) VALUES (:pid, :f, :cant, :mot)"
                    ), {"pid": prod_id, "f": fecha, "cant": float(excedente), "mot": "Sobreproducción"})
                    mermas_creadas += 1

        db.commit()

        # Opcional: dropear la columna vieja (comentado por seguridad)
        # db.execute(text("ALTER TABLE fact_ventas DROP COLUMN cantidad_producida"))
        # db.commit()

        resumen = {
            "status": "ok",
            "registros_migrados": creados,
            "mermas_creadas": mermas_creadas,
        }
        print(f"[MIGRACION] Completa: {resumen}")
        return resumen

    except Exception as e:
        db.rollback()
        print(f"[MIGRACION] Error: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    run_migracion()
