import sys
import os

target = r"d:\.UNT\2026-I\TESIS I\panaderia\backend\main.py"

with open(target, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Actualizar Schema
old_schema = """class VentaCreate(BaseModel):
    producto_id: int
    fecha: date
    cantidad_vendida: float
    cantidad_producida: Optional[float] = None"""

new_schema = """class VentaCreate(BaseModel):
    producto_id: int
    fecha: date
    cantidad_vendida: float
    cantidad_producida: Optional[float] = None
    motivo_merma: Optional[str] = "Sobreproduccion\""""

# 2. Actualizar Logica en crear_venta
old_logic = """    # Automatismo 1: Merma por sobreproduccion
    if cantidad_producida > venta.cantidad_vendida:
        excedente = round(cantidad_producida - venta.cantidad_vendida, 2)
        db.add(models.FactMerma(
            producto_id=venta.producto_id,
            fecha=venta.fecha,
            cantidad_merma=excedente,
            motivo="Sobreproduccion",
        ))
        merma_auto = excedente"""

new_logic = """    # Automatismo 1: Merma automatica por excedente
    if cantidad_producida > venta.cantidad_vendida:
        excedente = round(cantidad_producida - venta.cantidad_vendida, 2)
        motivo_final = venta.motivo_merma or "Sobreproduccion"
        db.add(models.FactMerma(
            producto_id=venta.producto_id,
            fecha=venta.fecha,
            cantidad_merma=excedente,
            motivo=motivo_final,
        ))
        merma_auto = f"{excedente} ({motivo_final})\""""

if old_schema in content:
    content = content.replace(old_schema, new_schema)
    print("Schema actualizado")

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    print("Logica actualizada")

with open(target, "w", encoding="utf-8") as f:
    f.write(content)
