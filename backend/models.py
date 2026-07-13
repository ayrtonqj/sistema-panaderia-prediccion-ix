from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, Boolean, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


# ==========================================
# DIMENSIONES (Contexto)
# ==========================================

class DimVendedor(Base):
    __tablename__ = "dim_vendedores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=True)
    dni = Column(String(8), unique=True, nullable=False)
    telefono = Column(String(15), nullable=True)
    email = Column(String(255), nullable=True)
    activo = Column(Boolean, default=True)
    username = Column(String(100), unique=True, nullable=True)
    password = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ventas = relationship("FactVenta", back_populates="vendedor")

class DimProducto(Base):
    __tablename__ = "dim_productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    categoria = Column(String(100), nullable=False)
    precio = Column(Float, nullable=False)
    costo = Column(Float, nullable=False)

    ventas = relationship("FactVenta", back_populates="producto")
    mermas = relationship("FactMerma", back_populates="producto")
    predicciones = relationship("FactPrediccion", back_populates="producto")
    recetas = relationship("FichaTecnica", back_populates="producto")
    produccion = relationship("FactProduccion", back_populates="producto")
    pan_pasado = relationship("PanPasado", back_populates="producto")


class DimClima(Base):
    __tablename__ = "dim_clima"
    # Esta tabla es vital para el Random Forest
    fecha = Column(Date, primary_key=True)
    temperatura_promedio = Column(Float, nullable=True)
    condicion = Column(String(50), nullable=True)   # Soleado, Nublado, Lluvia
    es_feriado = Column(Boolean, default=False)
    evento_especial = Column(String(100), nullable=True)  # Día de la Madre, etc.


class Proveedor(Base):
    __tablename__ = "dim_proveedores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    contacto = Column(String(255), nullable=True)
    telefono = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)

    ordenes = relationship("OrdenCompra", back_populates="proveedor")
    insumos = relationship("InsumoCritico", back_populates="proveedor_principal")
    insumos_precios = relationship("ProveedorInsumo", back_populates="proveedor")


class InsumoCritico(Base):
    __tablename__ = "insumos_criticos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    stock_actual = Column(Float, nullable=False)
    stock_minimo = Column(Float, nullable=False)
    unidad_medida = Column(String(50), nullable=False)  # Kg, Litros, Unidades
    # FK al proveedor principal → necesario para que n8n genere órdenes automáticas
    proveedor_id = Column(Integer, ForeignKey("dim_proveedores.id"), nullable=True, index=True)

    recetas = relationship("FichaTecnica", back_populates="insumo")
    ordenes = relationship("OrdenCompra", back_populates="insumo")
    proveedor_principal = relationship("Proveedor", back_populates="insumos")
    proveedores_precios = relationship("ProveedorInsumo", back_populates="insumo")


# ==========================================
# TABLA INTERMEDIA — Recetas (para n8n)
# ==========================================

class ProveedorInsumo(Base):
    __tablename__ = "proveedores_insumos"

    id = Column(Integer, primary_key=True, index=True)
    proveedor_id = Column(Integer, ForeignKey("dim_proveedores.id"), nullable=False, index=True)
    insumo_id = Column(Integer, ForeignKey("insumos_criticos.id"), nullable=False, index=True)
    precio_unitario = Column(Float, nullable=False)

    proveedor = relationship("Proveedor", back_populates="insumos_precios")
    insumo = relationship("InsumoCritico", back_populates="proveedores_precios")

    __table_args__ = (
        Index('ix_prov_insumo_unique', 'proveedor_id', 'insumo_id', unique=True),
    )


class TotpConfig(Base):
    __tablename__ = "totp_config"
    username = Column(String(100), primary_key=True)
    totp_secret = Column(String(64), nullable=False)
    totp_enabled = Column(Boolean, default=False)
    old_totp_secret = Column(String(64), nullable=True)


class FichaTecnica(Base):
    __tablename__ = "fichas_tecnicas"
    # Define cuánto insumo necesita cada producto por unidad producida
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("dim_productos.id"), nullable=False, index=True)
    insumo_id = Column(Integer, ForeignKey("insumos_criticos.id"), nullable=False, index=True)
    cantidad_necesaria = Column(Float, nullable=False)  # kg/litros por unidad de producto

    producto = relationship("DimProducto", back_populates="recetas")
    insumo = relationship("InsumoCritico", back_populates="recetas")

    __table_args__ = (
        Index('ix_fichas_tecnicas_prod_insumo', 'producto_id', 'insumo_id', unique=True),
    )


# ==========================================
# HECHOS (Transacciones)
# ==========================================

class FactVenta(Base):
    __tablename__ = "fact_ventas"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("dim_productos.id"), nullable=False, index=True)
    vendedor_id = Column(Integer, ForeignKey("dim_vendedores.id"), nullable=True, index=True)
    fecha = Column(Date, nullable=False, index=True)
    cantidad_vendida = Column(Float, nullable=False)
    precio_unitario = Column(Float, nullable=True)
    metodo_pago = Column(String(20), default='efectivo')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    producto = relationship("DimProducto", back_populates="ventas")
    vendedor = relationship("DimVendedor", back_populates="ventas")

    __table_args__ = (
        Index('ix_fact_ventas_prod_fecha', 'producto_id', 'fecha'),
    )


class FactMerma(Base):
    __tablename__ = "fact_mermas"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("dim_productos.id"), nullable=False, index=True)
    fecha = Column(Date, nullable=False, index=True)
    cantidad_merma = Column(Float, nullable=False)
    motivo = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    producto = relationship("DimProducto", back_populates="mermas")

    __table_args__ = (
        Index('ix_fact_mermas_prod_fecha', 'producto_id', 'fecha'),
    )


class FactProduccion(Base):
    __tablename__ = "fact_produccion"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("dim_productos.id"), nullable=False, index=True)
    fecha = Column(Date, nullable=False, index=True)
    cantidad_producida = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    producto = relationship("DimProducto", back_populates="produccion")

    __table_args__ = (
        Index('ix_fact_produccion_prod_fecha', 'producto_id', 'fecha'),
    )


class FactPrediccion(Base):
    __tablename__ = "fact_predicciones"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("dim_productos.id"), nullable=False, index=True)
    fecha_proyectada = Column(Date, nullable=False, index=True)
    demanda_estimada = Column(Float, nullable=False)
    # Confianza del modelo para reportar precisión en la tesis (OE6)
    confianza_prediccion = Column(Float, nullable=True)  # R² del modelo (0-1)
    algoritmo_utilizado = Column(String(100), nullable=True)  # Nombre del algoritmo usado
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    producto = relationship("DimProducto", back_populates="predicciones")

    __table_args__ = (
        Index('ix_fact_predicciones_prod_fecha', 'producto_id', 'fecha_proyectada'),
    )


class OrdenCompra(Base):
    __tablename__ = "fact_ordenes_compra"

    id = Column(Integer, primary_key=True, index=True)
    proveedor_id = Column(Integer, ForeignKey("dim_proveedores.id"), nullable=False, index=True)
    insumo_id = Column(Integer, ForeignKey("insumos_criticos.id"), nullable=False, index=True)
    fecha_orden = Column(Date, nullable=False)
    cantidad = Column(Float, nullable=False)
    precio_unitario = Column(Float, nullable=True)  # Para calcular costo de reposición
    estado = Column(String(50), nullable=False, default="pendiente", index=True)  # pendiente/confirmado/recibido/cancelado
    es_sugerida = Column(Boolean, default=False)  # Generada automáticamente por el sistema
    cantidad_sugerida_original = Column(Float, nullable=True)  # Cantidad que sugirió el sistema (para editar)
    fecha_necesaria = Column(Date, nullable=True)  # Fecha en que se necesita el insumo
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    proveedor = relationship("Proveedor", back_populates="ordenes")
    insumo = relationship("InsumoCritico", back_populates="ordenes")

    __table_args__ = (
        Index('ix_fact_ordenes_estado_fecha', 'estado', 'fecha_orden'),
    )


class PanPasado(Base):
    __tablename__ = "pan_pasado"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("dim_productos.id"), nullable=False, index=True)
    fecha_origen = Column(Date, nullable=False)
    cantidad = Column(Float, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    cantidad_vendida = Column(Float, default=0)
    estado = Column(String(20), default="disponible")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    producto = relationship("DimProducto", back_populates="pan_pasado")