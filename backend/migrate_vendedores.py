"""
Migración: agrega la tabla dim_vendedores y la columna vendedor_id a fact_ventas.
Uso: python migrate_vendedores.py
"""
from database import engine, SessionLocal
import models

def run():
    print("[Migración] Creando tabla dim_vendedores si no existe...")
    models.DimVendedor.__table__.create(bind=engine, checkfirst=True)

    print("[Migración] Agregando columna vendedor_id a fact_ventas si no existe...")
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("fact_ventas")]
    if "vendedor_id" not in columns:
        with engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE fact_ventas ADD COLUMN vendedor_id INTEGER REFERENCES dim_vendedores(id)"
            ))
            conn.commit()
        print("[OK] Columna vendedor_id agregada.")
    else:
        print("[OK] Columna vendedor_id ya existe.")

    print("[Migración] Insertando vendedores por defecto...")
    db = SessionLocal()
    try:
        existing = db.query(models.DimVendedor).count()
        if existing == 0:
            db.add_all([
                models.DimVendedor(nombre="Vendedor", apellido="Uno", dni="12345678", telefono="999111000", email="vendedor1@panaderia.com"),
                models.DimVendedor(nombre="Vendedor", apellido="Dos", dni="87654321", telefono="999222000", email="vendedor2@panaderia.com"),
            ])
            db.commit()
            print("[OK] Vendedores por defecto insertados.")
        else:
            print(f"[OK] Ya existen {existing} vendedor(es).")
    finally:
        db.close()

    print("[OK] Migración completada.")

if __name__ == "__main__":
    run()
