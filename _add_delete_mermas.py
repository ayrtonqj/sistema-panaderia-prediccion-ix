import os

target = r"d:\.UNT\2026-I\TESIS I\panaderia\backend\main.py"

with open(target, "r", encoding="utf-8") as f:
    content = f.read()

delete_merma_code = """
@app.delete("/mermas/{merma_id}")
def eliminar_merma(merma_id: int, db: Session = Depends(get_db)):
    \"\"\"Elimina un registro de merma.\"\"\"
    merma = db.query(models.FactMerma).filter(models.FactMerma.id == merma_id).first()
    if not merma:
        raise HTTPException(status_code=404, detail="Merma no encontrada")
    db.delete(merma)
    db.commit()
    return {"mensaje": f"Merma {merma_id} eliminada"}
"""

if "def eliminar_merma" not in content:
    # Insertar antes de "Analisis de Mermas"
    if "# -- Analisis de Mermas" in content:
        content = content.replace("# -- Analisis de Mermas", delete_merma_code + "\n# -- Analisis de Mermas")
    elif "# ── Análisis de Mermas" in content:
        content = content.replace("# ── Análisis de Mermas", delete_merma_code + "\n# ── Análisis de Mermas")
    else:
        content += delete_merma_code

with open(target, "w", encoding="utf-8") as f:
    f.write(content)
print("Endpoint DELETE /mermas/ agregado exitosamente.")
