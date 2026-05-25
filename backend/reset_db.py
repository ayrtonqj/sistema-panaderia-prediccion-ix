from database import engine
from models import Base

print("Borrando tablas antiguas...")
Base.metadata.drop_all(bind=engine)
print("Creando tablas nuevas con venta_id...")
Base.metadata.create_all(bind=engine)
print("¡Listo! La base de datos está actualizada.")
