from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import date, timedelta, datetime
from typing import Optional
import uuid
import models
from database import engine, SessionLocal
from ml.seed_data import PRODUCTOS, RECETAS, INSUMOS

models.Base.metadata.create_all(bind=engine)

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE fact_ventas ADD COLUMN IF NOT EXISTS metodo_pago VARCHAR(20) DEFAULT 'efectivo'"))
    conn.execute(text("ALTER TABLE fact_ordenes_compra ADD COLUMN IF NOT EXISTS es_sugerida BOOLEAN DEFAULT FALSE"))
    conn.execute(text("ALTER TABLE fact_ordenes_compra ADD COLUMN IF NOT EXISTS cantidad_sugerida_original FLOAT"))
    conn.execute(text("ALTER TABLE fact_ordenes_compra ADD COLUMN IF NOT EXISTS fecha_necesaria DATE"))
    conn.execute(text("ALTER TABLE dim_vendedores ADD COLUMN IF NOT EXISTS username VARCHAR(100) UNIQUE"))
    conn.execute(text("ALTER TABLE dim_vendedores ADD COLUMN IF NOT EXISTS password VARCHAR(100)"))
    conn.execute(text("UPDATE dim_vendedores SET username = telefono WHERE username IS NULL AND telefono IS NOT NULL"))
    conn.execute(text("UPDATE dim_vendedores SET password = dni WHERE password IS NULL"))
    conn.execute(text("ALTER TABLE fact_predicciones ADD COLUMN IF NOT EXISTS algoritmo_utilizado VARCHAR(100)"))
    conn.execute(text("CREATE TABLE IF NOT EXISTS totp_config (username VARCHAR(100) PRIMARY KEY, totp_secret VARCHAR(64) NOT NULL, totp_enabled BOOLEAN DEFAULT FALSE)"))
    conn.execute(text("ALTER TABLE totp_config ADD COLUMN IF NOT EXISTS old_totp_secret VARCHAR(64)"))
    conn.commit()

# Session tokens temporales para 2FA (username -> {token, expira})
SESSION_TOKENS = {}
# Intentos de verificación de setup 2FA (username -> contador)
VERIFY_2FA_ATTEMPTS = {}

app = FastAPI(title="Sistema Predictivo Panadería Victoria", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Schemas ──────────────────────────────────────────────────────────────────

class ProductoCreate(BaseModel):
    nombre: str
    categoria: str
    precio: float
    costo: float

class ProductoResponse(ProductoCreate):
    id: int
    class Config:
        from_attributes = True

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    categoria: Optional[str] = None
    precio: Optional[float] = None
    costo: Optional[float] = None

class VendedorCreate(BaseModel):
    nombre: str
    apellido: Optional[str] = None
    dni: str
    telefono: Optional[str] = None
    email: Optional[str] = None

class VendedorResponse(VendedorCreate):
    id: int
    activo: bool
    username: Optional[str] = None
    class Config:
        from_attributes = True

class VendedorUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    activo: Optional[bool] = None
    username: Optional[str] = None
    password: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class Login2FARequest(BaseModel):
    username: str
    session_token: str
    totp_code: str

class Setup2FARequest(BaseModel):
    username: str
    password: str

class Verify2FARequest(BaseModel):
    username: str
    totp_code: str

class Disable2FARequest(BaseModel):
    username: str
    password: str

class Recover2FARequest(BaseModel):
    username: str
    session_token: str
    password: str

class RecoverVerifyRequest(BaseModel):
    username: str
    session_token: str
    totp_code: str

class VentaCreate(BaseModel):
    producto_id: int
    fecha: date
    cantidad_vendida: float
    vendedor_id: Optional[int] = None

class VentaResponse(VentaCreate):
    id: int
    class Config:
        from_attributes = True

class VentaConProducto(BaseModel):
    id: int
    producto_id: int
    producto_nombre: str
    fecha: date
    cantidad_vendida: float
    vendedor_id: Optional[int] = None
    vendedor_nombre: Optional[str] = None
    class Config:
        from_attributes = True

class VentaRapidaCreate(BaseModel):
    producto_id: int
    cantidad_vendida: float
    vendedor_id: Optional[int] = None
    metodo_pago: str = 'efectivo'

class LoteVentaRapidaCreate(BaseModel):
    items: list[VentaRapidaCreate]

class MermaCreate(BaseModel):
    producto_id: int
    fecha: date
    cantidad_merma: float
    motivo: Optional[str] = None

class MermaResponse(MermaCreate):
    id: int
    class Config:
        from_attributes = True

class MermaConProducto(BaseModel):
    id: int
    producto_id: int
    producto_nombre: str
    fecha: date
    cantidad_merma: float
    motivo: Optional[str] = None
    class Config:
        from_attributes = True

class ProduccionCreate(BaseModel):
    producto_id: int
    fecha: date
    cantidad_producida: float

class ProduccionResponse(ProduccionCreate):
    id: int
    class Config:
        from_attributes = True

class SimulacionRequest(BaseModel):
    producto_id: int
    cantidad_actual: float
    cantidad_planeada: float

class ProduccionConProducto(BaseModel):
    id: int
    producto_id: int
    producto_nombre: str
    fecha: date
    cantidad_producida: float
    class Config:
        from_attributes = True

class InsumoCreate(BaseModel):
    nombre: str
    stock_actual: float
    stock_minimo: float
    unidad_medida: str
    proveedor_id: Optional[int] = None

class InsumoResponse(InsumoCreate):
    id: int
    class Config:
        from_attributes = True

class InsumoUpdate(BaseModel):
    stock_actual: Optional[float] = None
    stock_minimo: Optional[float] = None
    proveedor_id: Optional[int] = None

class InsumoAlerta(BaseModel):
    id: int
    nombre: str
    stock_actual: float
    stock_minimo: float
    unidad_medida: str
    necesita_reorden: bool
    proveedor_id: Optional[int] = None
    class Config:
        from_attributes = True

class InsumoDetalle(InsumoResponse):
    proveedor_nombre: Optional[str] = None
    consumo_promedio_diario: Optional[float] = None
    dias_restantes: Optional[int] = None
    ordenes_pendientes: int = 0

class AjusteStock(BaseModel):
    cantidad: float
    motivo: str

class PrediccionCreate(BaseModel):
    producto_id: int
    fecha_proyectada: date
    demanda_estimada: float
    confianza_prediccion: Optional[float] = None

class PrediccionResponse(PrediccionCreate):
    id: int
    class Config:
        from_attributes = True

class ClimaCreate(BaseModel):
    fecha: date
    temperatura_promedio: Optional[float] = None
    condicion: Optional[str] = None
    es_feriado: bool = False
    evento_especial: Optional[str] = None

class ClimaResponse(ClimaCreate):
    class Config:
        from_attributes = True

class ProductoActividad(BaseModel):
    id: int
    nombre: str
    categoria: str
    ultima_produccion: Optional[str] = None
    ultima_venta: Optional[str] = None
    dias_sin_producir: Optional[int] = None
    dias_sin_vender: Optional[int] = None

class FichaTecnicaCreate(BaseModel):
    producto_id: int
    insumo_id: int
    cantidad_necesaria: float

class FichaTecnicaResponse(FichaTecnicaCreate):
    id: int
    class Config:
        from_attributes = True

class FichaTecnicaDetallada(BaseModel):
    id: int
    producto_nombre: str
    insumo_nombre: str
    cantidad_necesaria: float
    class Config:
        from_attributes = True

class ProveedorCreate(BaseModel):
    nombre: str
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None

class ProveedorResponse(ProveedorCreate):
    id: int
    class Config:
        from_attributes = True

class OrdenCompraCreate(BaseModel):
    proveedor_id: int
    insumo_id: int
    fecha_orden: date
    cantidad: float
    precio_unitario: Optional[float] = None
    estado: str = "pendiente"
    es_sugerida: bool = False
    cantidad_sugerida_original: Optional[float] = None
    fecha_necesaria: Optional[date] = None

class OrdenCompraUpdate(BaseModel):
    cantidad: Optional[float] = None
    precio_unitario: Optional[float] = None
    proveedor_id: Optional[int] = None

class OrdenCompraResponse(OrdenCompraCreate):
    id: int
    class Config:
        from_attributes = True

class OrdenCompraDetallada(BaseModel):
    id: int
    proveedor_nombre: str
    insumo_nombre: str
    fecha_orden: date
    cantidad: float
    precio_unitario: Optional[float] = None
    estado: str
    es_sugerida: bool = False
    cantidad_sugerida_original: Optional[float] = None
    fecha_necesaria: Optional[date] = None
    class Config:
        from_attributes = True


# ── Root ─────────────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {
        "status": "online",
        "version": "2.0",
        "mensaje": "Sistema Predictivo Panadería Victoria — API activa",
        "endpoints_principales": [
            "/docs", "/dashboard/resumen",
            "/ml/entrenar", "/predicciones/generar",
            "/mermas/analisis", "/predicciones/vs-real"
        ]
    }


# ── Productos ────────────────────────────────────────────────────────────────

@app.post("/productos/", response_model=ProductoResponse)
def crear_producto(producto: ProductoCreate, db: Session = Depends(get_db)):
    db_prod = models.DimProducto(**producto.model_dump())
    db.add(db_prod)
    db.commit()
    db.refresh(db_prod)
    return db_prod

@app.get("/productos/", response_model=list[ProductoResponse])
def listar_productos(db: Session = Depends(get_db)):
    return db.query(models.DimProducto).all()

@app.get("/productos/{producto_id}", response_model=ProductoResponse)
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    prod = db.query(models.DimProducto).filter(models.DimProducto.id == producto_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return prod

@app.put("/productos/{producto_id}", response_model=ProductoResponse)
def actualizar_producto(producto_id: int, datos: ProductoUpdate, db: Session = Depends(get_db)):
    prod = db.query(models.DimProducto).filter(models.DimProducto.id == producto_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    for campo, valor in datos.model_dump(exclude_none=True).items():
        setattr(prod, campo, valor)
    db.commit()
    db.refresh(prod)
    return prod

@app.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    prod = db.query(models.DimProducto).filter(models.DimProducto.id == producto_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    db.delete(prod)
    db.commit()
    return {"mensaje": f"Producto {producto_id} eliminado"}

@app.post("/productos/migrate-add-missing")
def agregar_productos_faltantes(db: Session = Depends(get_db)):
    """Agrega los productos definidos en seed_data que aún no existen en la BD."""
    existentes = {p.nombre for p in db.query(models.DimProducto).all()}
    insumos_db = {ins.nombre: ins.id for ins in db.query(models.InsumoCritico).all()}
    agregados = 0
    recetas_agregadas = 0

    for idx, prod_data in enumerate(PRODUCTOS):
        if prod_data["nombre"] in existentes:
            continue
        prod = models.DimProducto(
            nombre=prod_data["nombre"],
            categoria=prod_data["categoria"],
            precio=prod_data["precio"],
            costo=prod_data["costo"],
        )
        db.add(prod)
        db.flush()
        agregados += 1

        if idx in RECETAS:
            for insumo_idx, cantidad in RECETAS[idx]:
                insumo_nombre = INSUMOS[insumo_idx]["nombre"]
                insumo_id = insumos_db.get(insumo_nombre)
                if insumo_id is None:
                    continue
                db.add(models.FichaTecnica(
                    producto_id=prod.id,
                    insumo_id=insumo_id,
                    cantidad_necesaria=cantidad,
                ))
                recetas_agregadas += 1

    db.commit()
    return {
        "productos_agregados": agregados,
        "recetas_agregadas": recetas_agregadas,
        "mensaje": f"{agregados} producto(s) agregado(s), {recetas_agregadas} receta(s) agregada(s)" if agregados > 0 else "Todos los productos ya existen",
    }

@app.get("/productos/actividad", response_model=list[ProductoActividad])
def actividad_productos(db: Session = Depends(get_db)):
    hoy = date.today()
    ult_prod = db.query(
        models.FactProduccion.producto_id,
        func.max(models.FactProduccion.fecha).label('ultima_fecha')
    ).group_by(models.FactProduccion.producto_id).all()
    prod_map = {r.producto_id: r.ultima_fecha for r in ult_prod}
    ult_venta = db.query(
        models.FactVenta.producto_id,
        func.max(models.FactVenta.fecha).label('ultima_fecha')
    ).group_by(models.FactVenta.producto_id).all()
    venta_map = {r.producto_id: r.ultima_fecha for r in ult_venta}
    productos = db.query(models.DimProducto).all()
    result = []
    for p in productos:
        up = prod_map.get(p.id)
        uv = venta_map.get(p.id)
        result.append(ProductoActividad(
            id=p.id,
            nombre=p.nombre,
            categoria=p.categoria,
            ultima_produccion=str(up) if up else None,
            ultima_venta=str(uv) if uv else None,
            dias_sin_producir=(hoy - up).days if up else None,
            dias_sin_vender=(hoy - uv).days if uv else None,
        ))
    return result


# ── Vendedores ───────────────────────────────────────────────────────────────

if False:
    @app.get("/vendedores/", response_model=list[VendedorResponse])
    def listar_vendedores(db: Session = Depends(get_db)):
        return db.query(models.DimVendedor).filter(models.DimVendedor.activo == True).all()

@app.get("/vendedores/todos", response_model=list[VendedorResponse])
def listar_vendedores_todos(db: Session = Depends(get_db)):
    return db.query(models.DimVendedor).all()

@app.get("/vendedores/ventas-hoy")
def ventas_hoy_por_vendedor(db: Session = Depends(get_db)):
    hoy = date.today()
    ventas = db.query(
        models.FactVenta.vendedor_id,
        models.DimVendedor.nombre.label("vendedor_nombre"),
        models.DimVendedor.apellido.label("vendedor_apellido"),
        func.sum(models.FactVenta.cantidad_vendida).label("total_unidades"),
        func.sum(models.FactVenta.cantidad_vendida * models.DimProducto.precio).label("total_ingreso"),
    ).join(models.DimVendedor, models.FactVenta.vendedor_id == models.DimVendedor.id
    ).join(models.DimProducto, models.FactVenta.producto_id == models.DimProducto.id
    ).filter(
        models.FactVenta.fecha == hoy,
        models.FactVenta.vendedor_id.isnot(None),
    ).group_by(
        models.FactVenta.vendedor_id,
        models.DimVendedor.nombre,
        models.DimVendedor.apellido,
    ).all()
    return [
        {
            "vendedor_id": v.vendedor_id,
            "nombre": f"{v.vendedor_nombre} {v.vendedor_apellido or ''}".strip(),
            "total_unidades": float(v.total_unidades),
            "total_ingreso": round(float(v.total_ingreso), 2),
        }
        for v in ventas
    ]

@app.post("/vendedores/", response_model=VendedorResponse)
def crear_vendedor(vendedor: VendedorCreate, db: Session = Depends(get_db)):
    data = vendedor.model_dump()
    data["username"] = vendedor.telefono or vendedor.dni
    data["password"] = vendedor.dni
    db_vendedor = models.DimVendedor(**data)
    db.add(db_vendedor)
    db.commit()
    db.refresh(db_vendedor)
    return db_vendedor

@app.get("/vendedores/{vendedor_id}", response_model=VendedorResponse)
def obtener_vendedor(vendedor_id: int, db: Session = Depends(get_db)):
    vendedor = db.query(models.DimVendedor).filter(models.DimVendedor.id == vendedor_id).first()
    if not vendedor:
        raise HTTPException(status_code=404, detail="Vendedor no encontrado")
    return vendedor

@app.put("/vendedores/{vendedor_id}", response_model=VendedorResponse)
def actualizar_vendedor(vendedor_id: int, datos: VendedorUpdate, db: Session = Depends(get_db)):
    vendedor = db.query(models.DimVendedor).filter(models.DimVendedor.id == vendedor_id).first()
    if not vendedor:
        raise HTTPException(status_code=404, detail="Vendedor no encontrado")
    update_data = datos.model_dump(exclude_none=True)
    if "telefono" in update_data:
        update_data["username"] = update_data["telefono"]
    if "dni" in update_data:
        update_data["password"] = update_data["dni"]
    for campo, valor in update_data.items():
        setattr(vendedor, campo, valor)
    db.commit()
    db.refresh(vendedor)
    return vendedor

@app.delete("/vendedores/{vendedor_id}")
def eliminar_vendedor(vendedor_id: int, db: Session = Depends(get_db)):
    vendedor = db.query(models.DimVendedor).filter(models.DimVendedor.id == vendedor_id).first()
    if not vendedor:
        raise HTTPException(status_code=404, detail="Vendedor no encontrado")
    nombre = vendedor.nombre
    n_ventas = db.query(models.FactVenta).filter(models.FactVenta.vendedor_id == vendedor_id).count()
    if n_ventas > 0:
        raise HTTPException(status_code=409, detail=f"No se puede eliminar: el vendedor tiene {n_ventas} venta(s) registrada(s). Desactívelo en vez de eliminarlo.")
    db.delete(vendedor)
    db.commit()
    return {"mensaje": f"Vendedor '{nombre}' eliminado correctamente."}

@app.post("/auth/login")
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    FIJOS = {
        "admin": {"rol": "administrador", "vendedor_id": None},
        "gerente": {"rol": "gerente", "vendedor_id": None},
        "cocina": {"rol": "cocina", "vendedor_id": None},
    }
    es_fijo = False
    rol = None
    vendedor_id = None

    if creds.username in FIJOS:
        if FIJOS[creds.username]["rol"] == creds.password or creds.username == creds.password:
            es_fijo = True
            rol = FIJOS[creds.username]["rol"]
            vendedor_id = FIJOS[creds.username]["vendedor_id"]

    if not es_fijo:
        vendedor = db.query(models.DimVendedor).filter(
            models.DimVendedor.username == creds.username,
            models.DimVendedor.password == creds.password,
            models.DimVendedor.activo == True,
        ).first()
        if vendedor:
            rol = "vendedor"
            vendedor_id = vendedor.id
        else:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Verificar si tiene 2FA configurado
    totp_row = db.query(models.TotpConfig).filter(
        models.TotpConfig.username == creds.username
    ).first()
    tiene_2fa = totp_row is not None and totp_row.totp_enabled

    if tiene_2fa:
        token = str(uuid.uuid4())
        SESSION_TOKENS[token] = {
            "username": creds.username,
            "expira": datetime.now() + timedelta(minutes=5),
            "intentos": 0,
        }
        return {
            "requiere_2fa": True,
            "session_token": token,
            "username": creds.username,
        }

    # Reparar: si existe registro pero totp_enabled=False (corrupto por recover-2fa viejo)
    if totp_row is not None and not totp_row.totp_enabled:
        import pyotp, qrcode, base64, io
        from PIL import Image

        totp_row.totp_enabled = True
        db.commit()

        pyotp_obj = pyotp.TOTP(totp_row.totp_secret)
        uri = pyotp_obj.provisioning_uri(creds.username, issuer_name="Panadería Victoria")
        qr = qrcode.QRCode(box_size=6, border=2)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode()

        token = str(uuid.uuid4())
        SESSION_TOKENS[token] = {
            "username": creds.username,
            "expira": datetime.now() + timedelta(minutes=5),
            "intentos": 0,
        }
        return {
            "requiere_2fa": True,
            "session_token": token,
            "username": creds.username,
            "qr_recovery": qr_b64,
        }

    # Primera vez: verificar si ya configuró 2FA alguna vez
    ya_tiene_secreto = totp_row is not None
    if not ya_tiene_secreto:
        return {
            "username": creds.username,
            "rol": rol,
            "vendedor_id": vendedor_id,
            "debe_configurar_2fa": True,
        }

    return {"username": creds.username, "rol": rol, "vendedor_id": vendedor_id}


@app.post("/auth/login-2fa")
def login_2fa(body: Login2FARequest, db: Session = Depends(get_db)):
    # Validar session token
    token_data = SESSION_TOKENS.get(body.session_token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Sesión expirada. Inicie sesión nuevamente.")
    if token_data["expira"] < datetime.now():
        del SESSION_TOKENS[body.session_token]
        raise HTTPException(status_code=401, detail="Token expirado. Inicie sesión nuevamente.")
    if token_data["username"] != body.username:
        raise HTTPException(status_code=401, detail="Token inválido.")

    # Obtener secreto TOTP
    totp_row = db.query(models.TotpConfig).filter(
        models.TotpConfig.username == body.username
    ).first()
    if not totp_row or not totp_row.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA no configurado.")

    import pyotp

    # Verificar código contra nuevo secreto
    totp_new = pyotp.TOTP(totp_row.totp_secret)
    code_valid = totp_new.verify(body.totp_code)

    # Si falla, probar contra viejo secreto (migración en curso)
    if not code_valid and totp_row.old_totp_secret:
        totp_old = pyotp.TOTP(totp_row.old_totp_secret)
        code_valid = totp_old.verify(body.totp_code)
        if code_valid:
            totp_row.old_totp_secret = None
            db.commit()

    token_data["intentos"] += 1
    if not code_valid:
        if token_data["intentos"] >= 3:
            del SESSION_TOKENS[body.session_token]
            raise HTTPException(status_code=429, detail="Demasiados intentos. Inicie sesión nuevamente.")
        raise HTTPException(status_code=401, detail=f"Código inválido. Intento {token_data['intentos']}/3.")

    # Login exitoso
    del SESSION_TOKENS[body.session_token]

    FIJOS = {"admin": "administrador", "gerente": "gerente", "cocina": "cocina"}
    if body.username in FIJOS:
        return {"username": body.username, "rol": FIJOS[body.username], "vendedor_id": None}

    v = db.query(models.DimVendedor).filter(
        models.DimVendedor.username == body.username,
        models.DimVendedor.activo == True,
    ).first()
    if v:
        return {"username": body.username, "rol": "vendedor", "vendedor_id": v.id}

    raise HTTPException(status_code=500, detail="Error al completar login.")


@app.post("/auth/setup-2fa")
def setup_2fa(body: Setup2FARequest, db: Session = Depends(get_db)):
    _verificar_credenciales(body.username, body.password, db)

    import pyotp, qrcode, base64, io
    from PIL import Image

    # Generar secreto TOTP
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(body.username, issuer_name="Panadería Victoria")

    # Generar QR en base64
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    # Guardar o reemplazar secreto (aún NO activo)
    existing = db.query(models.TotpConfig).filter(
        models.TotpConfig.username == body.username
    ).first()
    if existing:
        existing.totp_secret = secret
        existing.totp_enabled = False
        existing.old_totp_secret = None
    else:
        db.add(models.TotpConfig(username=body.username, totp_secret=secret, totp_enabled=False))
    db.commit()

    return {
        "secret": secret,
        "uri": uri,
        "qr_base64": qr_b64,
        "codigo_manual": secret,
    }


@app.post("/auth/verify-2fa")
def verify_2fa(body: Verify2FARequest, db: Session = Depends(get_db)):
    """Verifica código TOTP y activa 2FA. Máx 3 intentos de verificación."""
    import pyotp

    totp_row = db.query(models.TotpConfig).filter(
        models.TotpConfig.username == body.username
    ).first()
    if not totp_row:
        raise HTTPException(status_code=400, detail="Primero ejecute /auth/setup-2fa.")

    if totp_row.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA ya está activo.")

    # Contador de intentos (en memoria por username)
    VERIFY_2FA_ATTEMPTS[body.username] = VERIFY_2FA_ATTEMPTS.get(body.username, 0) + 1
    attempts = VERIFY_2FA_ATTEMPTS[body.username]

    totp = pyotp.TOTP(totp_row.totp_secret)
    if totp.verify(body.totp_code):
        VERIFY_2FA_ATTEMPTS[body.username] = 0
        totp_row.totp_enabled = True
        db.commit()
        return {"success": True, "mensaje": "2FA activado correctamente."}

    if attempts >= 3:
        VERIFY_2FA_ATTEMPTS[body.username] = 0
        # Eliminar secreto para que reinicie desde login
        db.delete(totp_row)
        db.commit()
        raise HTTPException(status_code=429, detail="Demasiados intentos. El QR ha sido invalidado. Inicie sesión nuevamente.")

    raise HTTPException(status_code=401, detail=f"Código inválido. Intento {attempts}/3.")


@app.post("/auth/recover-2fa")
def recover_2fa(body: Recover2FARequest, db: Session = Depends(get_db)):
    """Genera nuevo secreto TOTP y QR para re-vincular Google Authenticator.
    Requiere contraseña del usuario como prueba de identidad."""
    token_data = SESSION_TOKENS.get(body.session_token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Sesión expirada. Inicie sesión nuevamente.")
    if token_data["expira"] < datetime.now():
        del SESSION_TOKENS[body.session_token]
        raise HTTPException(status_code=401, detail="Token expirado. Inicie sesión nuevamente.")
    if token_data["username"] != body.username:
        raise HTTPException(status_code=401, detail="Token inválido.")

    _verificar_credenciales(body.username, body.password, db)

    import pyotp, qrcode, base64, io
    from PIL import Image

    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(body.username, issuer_name="Panadería Victoria")

    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    existing = db.query(models.TotpConfig).filter(
        models.TotpConfig.username == body.username
    ).first()
    if existing:
        existing.old_totp_secret = existing.totp_secret
        existing.totp_secret = secret
        existing.totp_enabled = True
    else:
        db.add(models.TotpConfig(username=body.username, totp_secret=secret, totp_enabled=True))
    db.commit()

    # Resetear contadores para recovery
    token_data["intentos_recover"] = 0

    return {"qr_base64": qr_b64, "codigo_manual": secret}


@app.post("/auth/recover-verify")
def recover_verify(body: RecoverVerifyRequest, db: Session = Depends(get_db)):
    """Verifica código TOTP del nuevo secreto y completa el login si es válido."""
    token_data = SESSION_TOKENS.get(body.session_token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Sesión expirada. Inicie sesión nuevamente.")
    if token_data["expira"] < datetime.now():
        del SESSION_TOKENS[body.session_token]
        raise HTTPException(status_code=401, detail="Token expirado. Inicie sesión nuevamente.")
    if token_data["username"] != body.username:
        raise HTTPException(status_code=401, detail="Token inválido.")

    totp_row = db.query(models.TotpConfig).filter(
        models.TotpConfig.username == body.username
    ).first()
    if not totp_row:
        raise HTTPException(status_code=400, detail="Primero ejecute /auth/recover-2fa.")

    import pyotp
    totp = pyotp.TOTP(totp_row.totp_secret)

    token_data["intentos_recover"] = token_data.get("intentos_recover", 0) + 1
    attempts = token_data["intentos_recover"]

    if totp.verify(body.totp_code):
        totp_row.old_totp_secret = None
        totp_row.totp_enabled = True
        db.commit()
        del SESSION_TOKENS[body.session_token]

        FIJOS = {"admin": "administrador", "gerente": "gerente", "cocina": "cocina"}
        if body.username in FIJOS:
            return {"username": body.username, "rol": FIJOS[body.username], "vendedor_id": None}
        v = db.query(models.DimVendedor).filter(
            models.DimVendedor.username == body.username,
            models.DimVendedor.activo == True,
        ).first()
        if v:
            return {"username": body.username, "rol": "vendedor", "vendedor_id": v.id}
        raise HTTPException(status_code=500, detail="Error al completar login.")

    if attempts >= 3:
        del SESSION_TOKENS[body.session_token]
        raise HTTPException(status_code=429, detail="Demasiados intentos. Inicie sesión nuevamente.")

    raise HTTPException(status_code=401, detail=f"Código inválido. Intento {attempts}/3.")


@app.post("/auth/disable-2fa")
def disable_2fa(body: Disable2FARequest, db: Session = Depends(get_db)):
    _verificar_credenciales(body.username, body.password, db)
    totp_row = db.query(models.TotpConfig).filter(
        models.TotpConfig.username == body.username
    ).first()
    if totp_row:
        db.delete(totp_row)
        db.commit()
    return {"success": True, "mensaje": "2FA desactivado."}


def _verificar_credenciales(username, password, db):
    FIJOS = {"admin": "administrador", "gerente": "gerente", "cocina": "cocina"}
    if username in FIJOS:
        if FIJOS[username] == password or username == password:
            return
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    v = db.query(models.DimVendedor).filter(
        models.DimVendedor.username == username,
        models.DimVendedor.password == password,
        models.DimVendedor.activo == True,
    ).first()
    if not v:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")


# ── Background: enviar PDF de orden confirmada por email ───────────────────────

def _orden_to_dict(orden, db):
    proveedor = db.query(models.Proveedor).filter(models.Proveedor.id == orden.proveedor_id).first()
    insumo = db.query(models.InsumoCritico).filter(models.InsumoCritico.id == orden.insumo_id).first()
    return {
        "id": orden.id,
        "proveedor": {
            "nombre": proveedor.nombre if proveedor else "—",
            "contacto": proveedor.contacto if proveedor else "—",
            "telefono": proveedor.telefono if proveedor else "—",
            "email": proveedor.email if proveedor else "—",
        } if proveedor else {"nombre": "—"},
        "insumo_nombre": insumo.nombre if insumo else "—",
        "insumo": {"nombre": insumo.nombre if insumo else "—"},
        "cantidad": orden.cantidad,
        "precio_unitario": orden.precio_unitario or 0,
        "estado": orden.estado,
        "fecha_orden": orden.fecha_orden,
        "fecha_necesaria": orden.fecha_necesaria,
    }


def enviar_pdf_orden_individual(orden_id: int):
    db = SessionLocal()
    try:
        from utils.pdf_orden import generar_pdf_orden
        from utils.email_utils import ADMIN_EMAIL, enviar_email_pdf

        orden = db.query(models.OrdenCompra).filter(models.OrdenCompra.id == orden_id).first()
        if not orden:
            return

        orden_data = _orden_to_dict(orden, db)
        pdf_bytes = generar_pdf_orden(orden_data)

        enviar_email_pdf(
            destinatario=ADMIN_EMAIL,
            asunto=f"Orden de Compra #{orden_id} Confirmada",
            cuerpo=f"La orden de compra #{orden_id} ha sido confirmada.\n\n"
                   f"Proveedor: {orden_data['proveedor']['nombre']}\n"
                   f"Insumo: {orden_data['insumo_nombre']}\n"
                   f"Cantidad: {orden.cantidad}\n"
                   f"Total: S/ {orden.cantidad * (orden.precio_unitario or 0):.2f}\n\n"
                   f"El PDF detallado se adjunta a este correo.",
            pdf_bytes=pdf_bytes,
            filename=f"orden_{orden_id}.pdf",
        )
    except Exception as e:
        print(f"[BG EMAIL] Error enviando PDF individual #{orden_id}: {e}")
    finally:
        db.close()


def enviar_pdf_sugerencias(orden_ids: list[int]):
    db = SessionLocal()
    try:
        from utils.pdf_orden import generar_pdf_sugeridas
        from utils.email_utils import ADMIN_EMAIL, enviar_email_pdf

        ordenes = db.query(models.OrdenCompra).filter(
            models.OrdenCompra.id.in_(orden_ids)
        ).order_by(models.OrdenCompra.id).all()

        if not ordenes:
            return

        ordenes_data = [_orden_to_dict(o, db) for o in ordenes]
        pdf_bytes = generar_pdf_sugeridas(ordenes_data)

        insumos_list = ", ".join(o["insumo_nombre"] for o in ordenes_data[:5])
        if len(ordenes_data) > 5:
            insumos_list += f" y {len(ordenes_data) - 5} mas"

        enviar_email_pdf(
            destinatario=ADMIN_EMAIL,
            asunto=f"{len(ordenes_data)} Orden(es) Sugerida(s) por Bajo Stock",
            cuerpo=f"Se han generado {len(ordenes_data)} orden(es) de compra sugeridas por bajo stock de insumos.\n\n"
                   f"Insumos: {insumos_list}\n\n"
                   f"El PDF consolidado se adjunta a este correo.\n\n"
                   f"Ingrese al sistema para revisar, editar y confirmar cada orden.",
            pdf_bytes=pdf_bytes,
            filename=f"ordenes_sugeridas_{date.today().strftime('%Y%m%d')}.pdf",
        )
    except Exception as e:
        print(f"[BG EMAIL] Error enviando PDF sugerencias: {e}")
    finally:
        db.close()


# ── Ventas ───────────────────────────────────────────────────────────────────

if False:
    @app.post("/ventas/")
    def crear_venta(venta: VentaCreate, db: Session = Depends(get_db)):
        """Registra una venta diaria."""
        if not db.query(models.DimProducto).filter(models.DimProducto.id == venta.producto_id).first():
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        db_venta = models.FactVenta(**venta.model_dump())
        db.add(db_venta)
        db.commit()
        db.refresh(db_venta)

        return {
            "id": db_venta.id,
            "producto_id": db_venta.producto_id,
            "fecha": str(db_venta.fecha),
            "cantidad_vendida": db_venta.cantidad_vendida,
        }

if False:
    @app.post("/ventas/rapida")
    def crear_venta_rapida(venta: VentaRapidaCreate, db: Session = Depends(get_db)):
        """Registro exprés para el vendedor: solo producto y cantidad, fecha = hoy."""
        if not db.query(models.DimProducto).filter(models.DimProducto.id == venta.producto_id).first():
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        db_venta = models.FactVenta(
            producto_id=venta.producto_id,
            fecha=date.today(),
            cantidad_vendida=venta.cantidad_vendida,
            vendedor_id=venta.vendedor_id,
        )
        db.add(db_venta)
        db.commit()
        db.refresh(db_venta)

        return {
            "id": db_venta.id,
            "producto_id": db_venta.producto_id,
            "vendedor_id": db_venta.vendedor_id,
            "fecha": str(db_venta.fecha),
            "cantidad_vendida": db_venta.cantidad_vendida,
        }

@app.post("/ventas/rapida/lote")
def crear_ventas_rapida_lote(lote: LoteVentaRapidaCreate, db: Session = Depends(get_db)):
    """Registra múltiples ventas exprés en una sola transacción."""
    ventas_creadas = []
    for item in lote.items:
        if not db.query(models.DimProducto).filter(models.DimProducto.id == item.producto_id).first():
            raise HTTPException(status_code=404, detail=f"Producto {item.producto_id} no encontrado")
        db_venta = models.FactVenta(
            producto_id=item.producto_id,
            fecha=date.today(),
            cantidad_vendida=item.cantidad_vendida,
            vendedor_id=item.vendedor_id,
            metodo_pago=item.metodo_pago,
        )
        db.add(db_venta)
        db.flush()
        ventas_creadas.append({
            "id": db_venta.id,
            "producto_id": db_venta.producto_id,
            "vendedor_id": db_venta.vendedor_id,
            "fecha": str(db_venta.fecha),
            "cantidad_vendida": db_venta.cantidad_vendida,
        })
    db.commit()
    return {"mensaje": f"{len(ventas_creadas)} ventas registradas", "ventas": ventas_creadas}

if False:
    @app.get("/ventas/", response_model=list[VentaConProducto])
    def listar_ventas(db: Session = Depends(get_db)):
        ventas = db.query(
            models.FactVenta.id,
            models.FactVenta.producto_id,
            models.DimProducto.nombre.label("producto_nombre"),
            models.FactVenta.fecha,
            models.FactVenta.cantidad_vendida,
            models.FactVenta.vendedor_id,
            models.DimVendedor.nombre.label("vendedor_nombre"),
        ).join(models.DimProducto).outerjoin(
            models.DimVendedor, models.FactVenta.vendedor_id == models.DimVendedor.id
        ).order_by(models.FactVenta.fecha.desc(), models.FactVenta.id.desc()).limit(150).all()
        return ventas


@app.get("/ventas/hoy")
def ventas_hoy(vendedor_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Ventas del día de hoy, agrupadas por producto, para el resumen del vendedor.
    Opcional: ?vendedor_id=X para filtrar por vendedor."""
    hoy = date.today()
    query = db.query(
        models.FactVenta.producto_id,
        models.DimProducto.nombre.label("producto_nombre"),
        models.DimProducto.precio,
        func.sum(models.FactVenta.cantidad_vendida).label("total_vendido"),
        func.count(models.FactVenta.id).label("transacciones"),
    ).join(models.DimProducto).filter(
        models.FactVenta.fecha == hoy
    )

    if vendedor_id is not None:
        query = query.filter(models.FactVenta.vendedor_id == vendedor_id)

    ventas = query.group_by(
        models.FactVenta.producto_id,
        models.DimProducto.nombre,
        models.DimProducto.precio,
    ).order_by(
        func.sum(models.FactVenta.cantidad_vendida).desc()
    ).all()

    return {
        "fecha": str(hoy),
        "vendedor_id": vendedor_id,
        "total_general": float(sum(v.total_vendido for v in ventas)),
        "productos": [
            {
                "producto_id": v.producto_id,
                "producto_nombre": v.producto_nombre,
                "precio": v.precio,
                "total_vendido": float(v.total_vendido),
                "transacciones": v.transacciones,
                "ingreso": round(v.total_vendido * v.precio, 2),
            }
            for v in ventas
        ],
    }

if False:
    @app.delete("/ventas/{venta_id}")
    def eliminar_venta(venta_id: int, db: Session = Depends(get_db)):
        """Elimina una venta."""
        venta = db.query(models.FactVenta).filter(models.FactVenta.id == venta_id).first()
        if not venta:
            raise HTTPException(status_code=404, detail="Venta no encontrada")

        db.delete(venta)
        db.commit()
        return {"mensaje": f"Venta {venta_id} eliminada."}


# ── Ventas Rápidas (resumen) ──────────────────────────────────────────────────


# ── Producción ─────────────────────────────────────────────────────────────────

@app.post("/produccion/")
def crear_produccion(produccion: ProduccionCreate, db: Session = Depends(get_db)):
    """
    Registra producción diaria con dos automatismos:
    1. MERMA AUTOMATICA: si producido > vendido en el día, genera FactMerma con motivo Sobreproducción.
    2. DESCUENTO DE STOCK: descuenta insumos según ficha técnica × cantidad_producida.
    """
    if not db.query(models.DimProducto).filter(models.DimProducto.id == produccion.producto_id).first():
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Guardar producción
    db_prod = models.FactProduccion(**produccion.model_dump())
    db.add(db_prod)
    db.flush()

    merma_auto = None
    stock_descontado = []

    # Automatismo 1: Merma automática por excedente (comparando con ventas del día)
    total_vendido_hoy = db.query(func.sum(models.FactVenta.cantidad_vendida)).filter(
        models.FactVenta.producto_id == produccion.producto_id,
        models.FactVenta.fecha == produccion.fecha,
    ).scalar() or 0

    if produccion.cantidad_producida > total_vendido_hoy:
        excedente = round(produccion.cantidad_producida - total_vendido_hoy, 2)
        db.add(models.FactMerma(
            producto_id=produccion.producto_id,
            fecha=produccion.fecha,
            cantidad_merma=excedente,
            motivo="Sobreproducción",
        ))
        merma_auto = f"{excedente} unidades (Sobreproducción)"

    # Automatismo 2: Validar stock antes de descontar
    if produccion.cantidad_producida > 0:
        fichas = db.query(models.FichaTecnica).filter(
            models.FichaTecnica.producto_id == produccion.producto_id
        ).all()
        insuficientes = []
        for ficha in fichas:
            insumo = db.query(models.InsumoCritico).filter(
                models.InsumoCritico.id == ficha.insumo_id
            ).first()
            if insumo:
                consumo = round(ficha.cantidad_necesaria * produccion.cantidad_producida, 4)
                if insumo.stock_actual < consumo:
                    insuficientes.append({
                        "insumo": insumo.nombre,
                        "disponible": insumo.stock_actual,
                        "necesario": consumo,
                        "faltante": round(consumo - insumo.stock_actual, 4),
                        "unidad": insumo.unidad_medida,
                    })
        if insuficientes:
            db.rollback()
            raise HTTPException(status_code=400, detail={
                "mensaje": "Stock insuficiente para producir",
                "insumos_faltantes": insuficientes,
            })

        for ficha in fichas:
            insumo = db.query(models.InsumoCritico).filter(
                models.InsumoCritico.id == ficha.insumo_id
            ).first()
            if insumo:
                consumo = round(ficha.cantidad_necesaria * produccion.cantidad_producida, 4)
                insumo.stock_actual = round(insumo.stock_actual - consumo, 4)
                stock_descontado.append({
                    "insumo": insumo.nombre,
                    "consumo": consumo,
                    "stock_restante": insumo.stock_actual,
                })

    db.commit()
    db.refresh(db_prod)

    return {
        "id": db_prod.id,
        "producto_id": db_prod.producto_id,
        "fecha": str(db_prod.fecha),
        "cantidad_producida": db_prod.cantidad_producida,
        "merma_auto_generada": merma_auto,
        "insumos_descontados": stock_descontado,
    }

@app.get("/produccion/", response_model=list[ProduccionConProducto])
def listar_produccion(db: Session = Depends(get_db)):
    return db.query(
        models.FactProduccion.id,
        models.FactProduccion.producto_id,
        models.DimProducto.nombre.label("producto_nombre"),
        models.FactProduccion.fecha,
        models.FactProduccion.cantidad_producida,
    ).join(models.DimProducto).order_by(
        models.FactProduccion.fecha.desc(), models.FactProduccion.id.desc()
    ).limit(150).all()

@app.get("/produccion/hoy")
def produccion_hoy(db: Session = Depends(get_db)):
    """Estado de producción de hoy para todos los productos."""
    hoy = date.today()
    productos = db.query(models.DimProducto).all()

    prod_hoy = db.query(
        models.FactProduccion.producto_id,
        func.sum(models.FactProduccion.cantidad_producida).label("total"),
    ).filter(models.FactProduccion.fecha == hoy).group_by(models.FactProduccion.producto_id).all()
    prod_dict = {p.producto_id: float(p.total) for p in prod_hoy}

    ventas_hoy = db.query(
        models.FactVenta.producto_id,
        func.sum(models.FactVenta.cantidad_vendida).label("total"),
    ).filter(models.FactVenta.fecha == hoy).group_by(models.FactVenta.producto_id).all()
    ventas_dict = {v.producto_id: float(v.total) for v in ventas_hoy}

    preds_hoy = db.query(models.FactPrediccion.producto_id).filter(
        models.FactPrediccion.fecha_proyectada == hoy
    ).all()
    pred_set = {p.producto_id for p in preds_hoy}

    return [
        {
            "producto_id": p.id,
            "producto_nombre": p.nombre,
            "categoria": p.categoria,
            "producido_hoy": prod_dict.get(p.id, 0),
            "vendido_hoy": ventas_dict.get(p.id, 0),
            "tiene_prediccion": p.id in pred_set,
        }
        for p in productos
    ]

@app.get("/produccion/sugerida")
def sugerir_produccion(db: Session = Depends(get_db)):
    """OE4: Sugiere cantidad a producir según predicción ML, ventas/producción de hoy y tasa histórica de merma."""
    hoy = date.today()
    desde_30 = hoy - timedelta(days=30)

    productos = db.query(models.DimProducto).all()

    # Predicciones para hoy
    preds_hoy = db.query(models.FactPrediccion).filter(
        models.FactPrediccion.fecha_proyectada == hoy
    ).all()
    pred_dict = {p.producto_id: p for p in preds_hoy}

    # Ventas de hoy
    ventas_hoy = db.query(
        models.FactVenta.producto_id,
        func.sum(models.FactVenta.cantidad_vendida).label("total"),
    ).filter(models.FactVenta.fecha == hoy).group_by(models.FactVenta.producto_id).all()
    ventas_dict = {v.producto_id: float(v.total) for v in ventas_hoy}

    # Producción de hoy
    prod_hoy = db.query(
        models.FactProduccion.producto_id,
        func.sum(models.FactProduccion.cantidad_producida).label("total"),
    ).filter(models.FactProduccion.fecha == hoy).group_by(models.FactProduccion.producto_id).all()
    prod_dict = {p.producto_id: float(p.total) for p in prod_hoy}

    # Mermas últimos 30 días por producto
    mermas_30d = db.query(
        models.FactMerma.producto_id,
        func.sum(models.FactMerma.cantidad_merma).label("total_merma"),
    ).filter(models.FactMerma.fecha >= desde_30).group_by(models.FactMerma.producto_id).all()
    merma_dict = {m.producto_id: float(m.total_merma) for m in mermas_30d}

    # Ventas últimos 30 días por producto
    ventas_30d = db.query(
        models.FactVenta.producto_id,
        func.sum(models.FactVenta.cantidad_vendida).label("total_ventas"),
    ).filter(models.FactVenta.fecha >= desde_30).group_by(models.FactVenta.producto_id).all()
    ventas_30d_dict = {v.producto_id: float(v.total_ventas) for v in ventas_30d}

    sugerencias = []
    for p in productos:
        pred = pred_dict.get(p.id)
        if not pred:
            continue

        demanda_est = pred.demanda_estimada
        vendido = ventas_dict.get(p.id, 0)
        producido = prod_dict.get(p.id, 0)

        total_merma = merma_dict.get(p.id, 0)
        total_ventas_30d = ventas_30d_dict.get(p.id, 0) or 1
        denom = total_ventas_30d + total_merma
        tasa_merma = round(total_merma / denom * 100, 1) if denom > 0 else 0

        sugerido = max(0, round(demanda_est * (1 + tasa_merma / 100) - vendido - producido))

        sugerencias.append({
            "producto_id": p.id,
            "producto_nombre": p.nombre,
            "demanda_estimada": demanda_est,
            "vendido_hoy": vendido,
            "producido_hoy": producido,
            "tasa_merma_historica_pct": tasa_merma,
            "produccion_sugerida": sugerido,
        })

    return sugerencias

if False:
    @app.delete("/produccion/{produccion_id}")
    def eliminar_produccion(produccion_id: int, db: Session = Depends(get_db)):
        """Elimina un registro de producción y recupera el stock de insumos."""
        prod = db.query(models.FactProduccion).filter(models.FactProduccion.id == produccion_id).first()
        if not prod:
            raise HTTPException(status_code=404, detail="Producción no encontrada")

        # Devolver stock de insumos
        cantidad = prod.cantidad_producida
        if cantidad > 0:
            fichas = db.query(models.FichaTecnica).filter(
                models.FichaTecnica.producto_id == prod.producto_id
            ).all()
            for ficha in fichas:
                insumo = db.query(models.InsumoCritico).filter(
                    models.InsumoCritico.id == ficha.insumo_id
                ).first()
                if insumo:
                    consumo = round(ficha.cantidad_necesaria * cantidad, 4)
                    insumo.stock_actual = round(insumo.stock_actual + consumo, 4)

        db.delete(prod)
        db.commit()
        return {"mensaje": f"Producción {produccion_id} eliminada. Stock recuperado."}


@app.post("/produccion/simular")
def simular_produccion(sim: SimulacionRequest, db: Session = Depends(get_db)):
    """Simula escenarios de producción: compara cantidad actual vs planeada, calcula impacto en insumos, costos y merma."""
    prod = db.query(models.DimProducto).filter(models.DimProducto.id == sim.producto_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Tasa de merma histórica (últimos 30 días)
    desde = date.today() - timedelta(days=30)
    total_merma = db.query(func.sum(models.FactMerma.cantidad_merma)).filter(
        models.FactMerma.producto_id == sim.producto_id,
        models.FactMerma.fecha >= desde,
    ).scalar() or 0
    total_ventas_30d = db.query(func.sum(models.FactVenta.cantidad_vendida)).filter(
        models.FactVenta.producto_id == sim.producto_id,
        models.FactVenta.fecha >= desde,
    ).scalar() or 1
    denom = total_ventas_30d + total_merma
    tasa_merma = round(total_merma / denom * 100, 1) if denom > 0 else 0

    # Insumos según ficha técnica
    fichas = db.query(models.FichaTecnica).filter(
        models.FichaTecnica.producto_id == sim.producto_id
    ).all()
    insumos = []
    for f in fichas:
        ins = db.query(models.InsumoCritico).filter(models.InsumoCritico.id == f.insumo_id).first()
        if ins:
            insumos.append({
                "insumo": ins.nombre,
                "unidad": ins.unidad_medida,
                "actual": round(f.cantidad_necesaria * sim.cantidad_actual, 4),
                "planeado": round(f.cantidad_necesaria * sim.cantidad_planeada, 4),
                "diferencia": round(f.cantidad_necesaria * (sim.cantidad_planeada - sim.cantidad_actual), 4),
            })

    def calc(cant):
        return {
            "cantidad": cant,
            "costo_produccion": round(cant * prod.costo, 2),
            "ingreso_estimado": round(cant * prod.precio, 2),
            "merma_estimada_uds": round(cant * tasa_merma / 100, 2),
            "merma_estimada_costos": round(cant * prod.costo * tasa_merma / 100, 2),
        }

    actual = calc(sim.cantidad_actual)
    planeado = calc(sim.cantidad_planeada)

    return {
        "producto": prod.nombre,
        "costo_unitario": prod.costo,
        "precio_unitario": prod.precio,
        "tasa_merma_historica_pct": tasa_merma,
        "actual": actual,
        "planeado": planeado,
        "diferencia": {
            "ahorro_insumos": round(actual["costo_produccion"] - planeado["costo_produccion"], 2),
            "merma_evitada_uds": round(actual["merma_estimada_uds"] - planeado["merma_estimada_uds"], 2),
            "merma_evitada_costos": round(actual["merma_estimada_costos"] - planeado["merma_estimada_costos"], 2),
        },
        "insumos_requeridos": insumos,
    }


# ── Mermas ───────────────────────────────────────────────────────────────────

@app.post("/mermas/", response_model=MermaResponse)
def crear_merma(merma: MermaCreate, db: Session = Depends(get_db)):
    if not db.query(models.DimProducto).filter(models.DimProducto.id == merma.producto_id).first():
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    db_merma = models.FactMerma(**merma.model_dump())
    db.add(db_merma)
    db.commit()
    db.refresh(db_merma)
    return db_merma

@app.get("/mermas/", response_model=list[MermaConProducto])
def listar_mermas(db: Session = Depends(get_db)):
    return db.query(
        models.FactMerma.id,
        models.FactMerma.producto_id,
        models.DimProducto.nombre.label("producto_nombre"),
        models.FactMerma.fecha,
        models.FactMerma.cantidad_merma,
        models.FactMerma.motivo,
    ).join(models.DimProducto).order_by(models.FactMerma.fecha.desc(), models.FactMerma.id.desc()).limit(150).all()

@app.get("/mermas/analisis")
def analisis_mermas(db: Session = Depends(get_db)):
    """OE1: Agrupación de mermas por motivo y por producto — ahora incluye costo económico."""
    # Por motivo (con costo)
    por_motivo = db.query(
        models.FactMerma.motivo,
        func.count(models.FactMerma.id).label("frecuencia"),
        func.sum(models.FactMerma.cantidad_merma).label("total_merma"),
        func.sum(models.FactMerma.cantidad_merma * models.DimProducto.costo).label("perdida_economica"),
    ).join(models.DimProducto).group_by(models.FactMerma.motivo).order_by(
        func.sum(models.FactMerma.cantidad_merma).desc()
    ).all()

    # Por producto (con costo)
    por_producto = db.query(
        models.DimProducto.nombre.label("producto"),
        func.sum(models.FactMerma.cantidad_merma).label("total_merma"),
        func.count(models.FactMerma.id).label("frecuencia"),
        models.DimProducto.costo.label("costo_unitario"),
        func.sum(models.FactMerma.cantidad_merma * models.DimProducto.costo).label("perdida_economica"),
    ).join(models.DimProducto).group_by(models.DimProducto.nombre, models.DimProducto.costo).order_by(
        func.sum(models.FactMerma.cantidad_merma).desc()
    ).all()

    # Totales globales
    total_ventas = db.query(func.sum(models.FactVenta.cantidad_vendida)).scalar() or 1
    total_mermas = db.query(func.sum(models.FactMerma.cantidad_merma)).scalar() or 0
    pct_merma = round((total_mermas / (total_ventas + total_mermas)) * 100, 2)

    perdida_total = db.query(
        func.sum(models.FactMerma.cantidad_merma * models.DimProducto.costo)
    ).join(models.DimProducto).scalar() or 0

    return {
        "porcentaje_merma_global": pct_merma,
        "total_unidades_merma": total_mermas,
        "perdida_economica_total": round(float(perdida_total), 2),
        "por_motivo": [
            {
                "motivo": r.motivo or "Sin motivo",
                "frecuencia": r.frecuencia,
                "total_merma": float(r.total_merma),
                "perdida_economica": round(float(r.perdida_economica), 2),
            }
            for r in por_motivo
        ],
        "por_producto": [
            {
                "producto": r.producto,
                "total_merma": float(r.total_merma),
                "frecuencia": r.frecuencia,
                "costo_unitario": float(r.costo_unitario),
                "perdida_economica": round(float(r.perdida_economica), 2),
            }
            for r in por_producto
        ],
    }


# ── Insumos ──────────────────────────────────────────────────────────────────

@app.post("/insumos/", response_model=InsumoResponse)
def crear_insumo(insumo: InsumoCreate, db: Session = Depends(get_db)):
    db_insumo = models.InsumoCritico(**insumo.model_dump())
    db.add(db_insumo)
    db.commit()
    db.refresh(db_insumo)
    return db_insumo

@app.get("/insumos/", response_model=list[InsumoDetalle])
def listar_insumos(db: Session = Depends(get_db)):
    hace_30 = date.today() - timedelta(days=30)
    consumo = db.query(
        models.FichaTecnica.insumo_id,
        (func.sum(models.FichaTecnica.cantidad_necesaria * models.FactProduccion.cantidad_producida) / 30).label('consumo_diario')
    ).join(
        models.FactProduccion,
        models.FichaTecnica.producto_id == models.FactProduccion.producto_id
    ).filter(
        models.FactProduccion.fecha >= hace_30
    ).group_by(models.FichaTecnica.insumo_id).all()
    cons_map = {r.insumo_id: float(r.consumo_diario) for r in consumo}
    ordenes_pend = db.query(
        models.OrdenCompra.insumo_id,
        func.count(models.OrdenCompra.id).label('total')
    ).filter(models.OrdenCompra.estado == 'pendiente').group_by(models.OrdenCompra.insumo_id).all()
    ord_map = {r.insumo_id: r.total for r in ordenes_pend}
    insumos = db.query(models.InsumoCritico).all()
    result = []
    for i in insumos:
        cd = cons_map.get(i.id, 0)
        result.append(InsumoDetalle(
            id=i.id, nombre=i.nombre,
            stock_actual=i.stock_actual, stock_minimo=i.stock_minimo,
            unidad_medida=i.unidad_medida,
            proveedor_id=i.proveedor_id,
            proveedor_nombre=i.proveedor_principal.nombre if i.proveedor_principal else None,
            consumo_promedio_diario=round(cd, 4) if cd else None,
            dias_restantes=int(i.stock_actual / cd) if cd and cd > 0 and i.stock_actual > 0 else None,
            ordenes_pendientes=ord_map.get(i.id, 0),
        ))
    return result

@app.put("/insumos/{insumo_id}", response_model=InsumoResponse)
def actualizar_insumo(insumo_id: int, datos: InsumoUpdate, db: Session = Depends(get_db)):
    insumo = db.query(models.InsumoCritico).filter(models.InsumoCritico.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    for campo, valor in datos.model_dump(exclude_none=True).items():
        setattr(insumo, campo, valor)
    db.commit()
    db.refresh(insumo)
    return insumo

@app.get("/insumos/alertas/", response_model=list[InsumoAlerta])
def obtener_alertas_insumos(db: Session = Depends(get_db)):
    insumos = db.query(models.InsumoCritico).all()
    return [
        InsumoAlerta(
            id=i.id, nombre=i.nombre,
            stock_actual=i.stock_actual, stock_minimo=i.stock_minimo,
            unidad_medida=i.unidad_medida,
            necesita_reorden=i.stock_actual < i.stock_minimo,
            proveedor_id=i.proveedor_id,
        )
        for i in insumos
    ]

@app.delete("/insumos/{insumo_id}")
def eliminar_insumo(insumo_id: int, db: Session = Depends(get_db)):
    """Elimina un insumo si no tiene fichas técnicas ni órdenes de compra activas."""
    insumo = db.query(models.InsumoCritico).filter(
        models.InsumoCritico.id == insumo_id
    ).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")

    # Protección referencial: fichas técnicas (recetas)
    n_fichas = db.query(models.FichaTecnica).filter(
        models.FichaTecnica.insumo_id == insumo_id
    ).count()
    if n_fichas > 0:
        raise HTTPException(
            status_code=409,
            detail=f"No se puede eliminar: el insumo está en {n_fichas} ficha(s) técnica(s)."
        )

    # Protección referencial: órdenes de compra pendientes
    n_ordenes = db.query(models.OrdenCompra).filter(
        models.OrdenCompra.insumo_id == insumo_id,
        models.OrdenCompra.estado == "pendiente"
    ).count()
    if n_ordenes > 0:
        raise HTTPException(
            status_code=409,
            detail=f"No se puede eliminar: hay {n_ordenes} orden(es) pendiente(s) para este insumo."
        )

    nombre = insumo.nombre
    db.delete(insumo)
    db.commit()
    return {"mensaje": f"Insumo '{nombre}' eliminado correctamente."}

@app.get("/proveedores/")
def listar_proveedores(db: Session = Depends(get_db)):
    return db.query(models.Proveedor).all()

@app.post("/insumos/{insumo_id}/ajustar")
def ajustar_stock(insumo_id: int, ajuste: AjusteStock, db: Session = Depends(get_db)):
    insumo = db.query(models.InsumoCritico).filter(models.InsumoCritico.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    insumo.stock_actual = round(insumo.stock_actual + ajuste.cantidad, 4)
    if insumo.stock_actual < 0:
        db.rollback()
        raise HTTPException(status_code=400, detail="El stock no puede ser negativo")
    db.commit()
    return {"mensaje": f"Stock ajustado: {ajuste.cantidad:+.2f} {insumo.unidad_medida}", "stock_nuevo": insumo.stock_actual}


# ── Predicciones ─────────────────────────────────────────────────────────────

@app.get("/predicciones/", response_model=list[PrediccionResponse])
def listar_predicciones(db: Session = Depends(get_db)):
    return db.query(models.FactPrediccion).order_by(
        models.FactPrediccion.fecha_proyectada.desc()
    ).limit(150).all()

@app.post("/predicciones/generar")
async def generar_predicciones(n_dias: int = 7, db: Session = Depends(get_db)):
    """OE2/OE3: Ejecuta el modelo ML y guarda predicciones en BD."""
    try:
        from ml.predictor import generar_predicciones as _predecir
        resultado = await _predecir(n_dias=n_dias)
        return resultado
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar predicciones: {str(e)}")



# ── Clima ────────────────────────────────────────────────────────────────────

if False:
    @app.post("/clima/", response_model=ClimaResponse)
    def crear_clima(clima: ClimaCreate, db: Session = Depends(get_db)):
        db_clima = models.DimClima(**clima.model_dump())
        db.add(db_clima)
        db.commit()
        db.refresh(db_clima)
        return db_clima

if False:
    @app.get("/clima/", response_model=list[ClimaResponse])
    def listar_clima(db: Session = Depends(get_db)):
        return db.query(models.DimClima).order_by(models.DimClima.fecha.desc()).limit(30).all()

@app.get("/clima/{fecha}", response_model=ClimaResponse)
def obtener_clima(fecha: date, db: Session = Depends(get_db)):
    clima = db.query(models.DimClima).filter(models.DimClima.fecha == fecha).first()
    if not clima:
        raise HTTPException(status_code=404, detail="Clima no encontrado para esa fecha")
    return clima


# ── Fichas Técnicas ───────────────────────────────────────────────────────────

@app.post("/fichas-tecnicas/", response_model=FichaTecnicaResponse)
def crear_ficha_tecnica(ficha: FichaTecnicaCreate, db: Session = Depends(get_db)):
    if not db.query(models.DimProducto).filter(models.DimProducto.id == ficha.producto_id).first():
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if not db.query(models.InsumoCritico).filter(models.InsumoCritico.id == ficha.insumo_id).first():
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    db_ficha = models.FichaTecnica(**ficha.model_dump())
    db.add(db_ficha)
    db.commit()
    db.refresh(db_ficha)
    return db_ficha

@app.get("/fichas-tecnicas/", response_model=list[FichaTecnicaDetallada])
def listar_fichas_tecnicas(db: Session = Depends(get_db)):
    return db.query(
        models.FichaTecnica.id,
        models.DimProducto.nombre.label("producto_nombre"),
        models.InsumoCritico.nombre.label("insumo_nombre"),
        models.FichaTecnica.cantidad_necesaria,
    ).join(models.DimProducto).join(models.InsumoCritico).all()


# ── Proveedores ───────────────────────────────────────────────────────────────

@app.post("/proveedores/", response_model=ProveedorResponse)
def crear_proveedor(proveedor: ProveedorCreate, db: Session = Depends(get_db)):
    db_prov = models.Proveedor(**proveedor.model_dump())
    db.add(db_prov)
    db.commit()
    db.refresh(db_prov)
    return db_prov

@app.get("/proveedores/", response_model=list[ProveedorResponse])
def listar_proveedores(db: Session = Depends(get_db)):
    return db.query(models.Proveedor).all()


# ── Órdenes de Compra ─────────────────────────────────────────────────────────

@app.post("/ordenes-compra/", response_model=OrdenCompraResponse)
def crear_orden_compra(orden: OrdenCompraCreate, db: Session = Depends(get_db)):
    if not db.query(models.Proveedor).filter(models.Proveedor.id == orden.proveedor_id).first():
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    if not db.query(models.InsumoCritico).filter(models.InsumoCritico.id == orden.insumo_id).first():
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    db_orden = models.OrdenCompra(**orden.model_dump())
    db.add(db_orden)
    db.commit()
    db.refresh(db_orden)
    return db_orden

@app.get("/ordenes-compra/", response_model=list[OrdenCompraDetallada])
def listar_ordenes_compra(db: Session = Depends(get_db)):
    rows = db.query(
        models.OrdenCompra.id,
        models.Proveedor.nombre.label("proveedor_nombre"),
        models.InsumoCritico.nombre.label("insumo_nombre"),
        models.OrdenCompra.fecha_orden,
        models.OrdenCompra.cantidad,
        models.OrdenCompra.precio_unitario,
        models.OrdenCompra.estado,
        models.OrdenCompra.es_sugerida,
        models.OrdenCompra.cantidad_sugerida_original,
        models.OrdenCompra.fecha_necesaria,
    ).select_from(models.OrdenCompra).join(
        models.Proveedor, models.OrdenCompra.proveedor_id == models.Proveedor.id
    ).join(
        models.InsumoCritico, models.OrdenCompra.insumo_id == models.InsumoCritico.id
    ).order_by(models.OrdenCompra.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "proveedor_nombre": r.proveedor_nombre,
            "insumo_nombre": r.insumo_nombre,
            "fecha_orden": r.fecha_orden,
            "cantidad": r.cantidad,
            "precio_unitario": r.precio_unitario,
            "estado": r.estado,
            "es_sugerida": r.es_sugerida,
            "cantidad_sugerida_original": r.cantidad_sugerida_original,
            "fecha_necesaria": r.fecha_necesaria,
        }
        for r in rows
    ]

@app.put("/ordenes-compra/{orden_id}")
def editar_orden_compra(orden_id: int, datos: OrdenCompraUpdate, db: Session = Depends(get_db)):
    orden = db.query(models.OrdenCompra).filter(models.OrdenCompra.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if orden.estado != "pendiente":
        raise HTTPException(status_code=400, detail="Solo se pueden editar órdenes pendientes")
    if datos.cantidad is not None:
        orden.cantidad = datos.cantidad
    if datos.precio_unitario is not None:
        orden.precio_unitario = datos.precio_unitario
    if datos.proveedor_id is not None:
        if not db.query(models.Proveedor).filter(models.Proveedor.id == datos.proveedor_id).first():
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        orden.proveedor_id = datos.proveedor_id
    db.commit()
    return {"mensaje": f"Orden {orden_id} actualizada"}

@app.post("/ordenes-compra/{orden_id}/confirmar")
def confirmar_orden_compra(orden_id: int, bg_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    orden = db.query(models.OrdenCompra).filter(models.OrdenCompra.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if orden.estado != "pendiente":
        raise HTTPException(status_code=400, detail="Solo se pueden confirmar órdenes pendientes")
    orden.estado = "confirmado"
    db.commit()
    bg_tasks.add_task(enviar_pdf_orden_individual, orden_id)
    return {"mensaje": f"Orden {orden_id} confirmada", "estado": "confirmado"}

@app.post("/ordenes-compra/{orden_id}/cancelar")
def cancelar_orden_compra(orden_id: int, db: Session = Depends(get_db)):
    orden = db.query(models.OrdenCompra).filter(models.OrdenCompra.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if orden.estado in ["recibido", "cancelado"]:
        raise HTTPException(status_code=400, detail="La orden ya fue recibida o cancelada")
    orden.estado = "cancelado"
    db.commit()
    return {"mensaje": f"Orden {orden_id} cancelada", "estado": "cancelado"}

@app.post("/ordenes-compra/sugerir")
def sugerir_ordenes_compra(bg_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Genera órdenes de compra sugeridas para insumos con stock < mínimo.
    Calcula la cantidad necesaria según predicciones ML para mañana."""
    manana = date.today() + timedelta(days=1)
    insumos = db.query(models.InsumoCritico).all()
    hoy = date.today()
    creadas = 0

    predicciones_manana = db.query(models.FactPrediccion).filter(
        models.FactPrediccion.fecha_proyectada == manana
    ).all()
    pred_dict = {p.producto_id: p.demanda_estimada for p in predicciones_manana}

    fichas = db.query(models.FichaTecnica).all()
    consumo_por_insumo = {}
    for f in fichas:
        demanda = pred_dict.get(f.producto_id, 0)
        if demanda > 0:
            consumo_por_insumo[f.insumo_id] = consumo_por_insumo.get(f.insumo_id, 0) + (f.cantidad_necesaria * demanda)

    ids_creados = []

    for insumo in insumos:
        if insumo.stock_actual >= insumo.stock_minimo:
            continue
        if not insumo.proveedor_id:
            continue

        necesidad_manana = consumo_por_insumo.get(insumo.id, 0)
        cantidad_sugerida = max(
            insumo.stock_minimo * 2 - insumo.stock_actual,
            necesidad_manana - insumo.stock_actual,
            0
        )
        if cantidad_sugerida <= 0:
            continue

        existe_pendiente = db.query(models.OrdenCompra).filter(
            models.OrdenCompra.insumo_id == insumo.id,
            models.OrdenCompra.estado.in_(["pendiente", "confirmado"]),
        ).first()
        if existe_pendiente:
            continue

        nueva = models.OrdenCompra(
            proveedor_id=insumo.proveedor_id,
            insumo_id=insumo.id,
            fecha_orden=hoy,
            cantidad=cantidad_sugerida,
            estado="pendiente",
            es_sugerida=True,
            cantidad_sugerida_original=cantidad_sugerida,
            fecha_necesaria=manana,
        )
        db.add(nueva)
        db.flush()
        ids_creados.append(nueva.id)
        creadas += 1

    db.commit()

    if ids_creados:
        bg_tasks.add_task(enviar_pdf_sugerencias, ids_creados)

    return {"ordenes_sugeridas": creadas, "mensaje": f"{creadas} orden(es) sugerida(s) creada(s)" if creadas else "Todos los insumos tienen stock suficiente"}

@app.post("/ordenes-compra/sugerir-urgente")
def sugerir_ordenes_urgente(body: list[dict], db: Session = Depends(get_db)):
    """Crea órdenes de compra sugeridas para insumos específicos que faltaron en producción."""
    manana = date.today() + timedelta(days=1)
    hoy = date.today()
    creadas = 0

    for item in body:
        nombre = item.get("insumo", "")
        faltante = item.get("faltante", 0)
        if not nombre or faltante <= 0:
            continue

        insumo = db.query(models.InsumoCritico).filter(
            models.InsumoCritico.nombre == nombre
        ).first()
        if not insumo or not insumo.proveedor_id:
            continue

        existe = db.query(models.OrdenCompra).filter(
            models.OrdenCompra.insumo_id == insumo.id,
            models.OrdenCompra.estado.in_(["pendiente", "confirmado"]),
        ).first()
        if existe:
            continue

        cantidad = max(faltante, insumo.stock_minimo * 2 - insumo.stock_actual)
        db.add(models.OrdenCompra(
            proveedor_id=insumo.proveedor_id,
            insumo_id=insumo.id,
            fecha_orden=hoy,
            cantidad=cantidad,
            estado="pendiente",
            es_sugerida=True,
            cantidad_sugerida_original=cantidad,
            fecha_necesaria=manana,
        ))
        creadas += 1

    db.commit()
    return {"ordenes_sugeridas": creadas, "mensaje": f"{creadas} orden(es) sugerida(s) creada(s)" if creadas else "No se crearon órdenes"}

@app.post("/ordenes-compra/{orden_id}/recibir")
def recibir_orden(orden_id: int, db: Session = Depends(get_db)):
    """Recibe una orden de compra y aumenta el stock del insumo."""
    orden = db.query(models.OrdenCompra).filter(models.OrdenCompra.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    if orden.estado == "recibido":
        return {"mensaje": "La orden ya fue recibida anteriormente", "estado": "recibido"}
    
    # Obtener el insumo y aumentar stock
    insumo = db.query(models.InsumoCritico).filter(models.InsumoCritico.id == orden.insumo_id).first()
    if insumo:
        insumo.stock_actual = round(insumo.stock_actual + orden.cantidad, 4)
        stock_anterior = insumo.stock_actual - orden.cantidad
        stock_nuevo = insumo.stock_actual
    else:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    
    # Actualizar estado de la orden
    orden.estado = "recibido"
    db.commit()
    
    return {
        "mensaje": f"Orden {orden_id} recibida correctamente",
        "insumo": insumo.nombre,
        "cantidad_recibida": orden.cantidad,
        "stock_anterior": stock_anterior,
        "stock_nuevo": stock_nuevo,
        "estado": "recibido"
    }

# ── Validación de Predicciones (OE6) ──────────────────────────────────────────

@app.get("/predicciones/vs-real")
def obtener_comparacion_predicciones(dias: int = 30, db: Session = Depends(get_db)):
    fecha_limite = date.today() - timedelta(days=dias)
    # Buscar pares de (Predicción, Venta) para el mismo producto y fecha
    pares = db.query(models.FactPrediccion, models.FactVenta, models.DimProducto.nombre)\
              .join(models.FactVenta, 
                    (models.FactPrediccion.producto_id == models.FactVenta.producto_id) & 
                    (models.FactPrediccion.fecha_proyectada == models.FactVenta.fecha))\
              .join(models.DimProducto, models.FactPrediccion.producto_id == models.DimProducto.id)\
              .filter(models.FactPrediccion.fecha_proyectada >= fecha_limite)\
              .all()
    
    res = []
    for p, v, nombre in pares:
        res.append({
            "producto_nombre": nombre,
            "fecha": p.fecha_proyectada,
            "predicho": p.demanda_estimada,
            "real": v.cantidad_vendida
        })
    
    if not res:
        return {"mae_global": 0, "detalle": []}
    
    mae_global = sum(abs(x["predicho"] - x["real"]) for x in res) / len(res)
    return {"mae_global": mae_global, "detalle": res}


@app.get("/predicciones/recomendaciones")
def recomendaciones_modelo(db: Session = Depends(get_db)):
    """Genera recomendaciones contextuales basadas en predicciones ML, clima y factores estacionales."""
    hoy = date.today()

    # Predicciones próximos 7 días
    preds = db.query(
        models.FactPrediccion, models.DimProducto.nombre, models.DimProducto.id,
    ).join(models.DimProducto).filter(
        models.FactPrediccion.fecha_proyectada >= hoy,
        models.FactPrediccion.fecha_proyectada <= hoy + timedelta(days=7),
    ).order_by(models.FactPrediccion.fecha_proyectada).all()

    if not preds:
        return {"fecha_generacion": str(hoy), "recomendaciones": []}

    # Promedio histórico por día de semana (por producto)
    desde_hist = hoy - timedelta(days=90)
    hist = db.query(
        models.FactVenta.producto_id,
        func.extract("dow", models.FactVenta.fecha).label("dia_semana"),
        func.avg(models.FactVenta.cantidad_vendida).label("promedio"),
    ).filter(models.FactVenta.fecha >= desde_hist).group_by(
        models.FactVenta.producto_id, func.extract("dow", models.FactVenta.fecha)
    ).all()

    prom_dict = {}
    for r in hist:
        prom_dict.setdefault(int(r.producto_id), {})[int(r.dia_semana)] = float(r.promedio)

    # Clima en los próximos días
    climas = db.query(models.DimClima).filter(
        models.DimClima.fecha >= hoy,
        models.DimClima.fecha <= hoy + timedelta(days=7),
    ).all()
    clima_dict = {str(c.fecha): c for c in climas}

    recomendaciones = []
    for pred, prod_nombre, prod_id in preds:
        fecha_dt = pred.fecha_proyectada
        fecha_str = str(fecha_dt)
        dia_semana = fecha_dt.weekday()

        promedio = prom_dict.get(prod_id, {}).get(dia_semana)
        if not promedio or promedio == 0:
            continue

        dif_pct = round((pred.demanda_estimada - promedio) / promedio * 100, 0)

        if abs(dif_pct) < 20:
            continue

        # Determinar factor
        dia_nombres = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        dia_nombre = dia_nombres[dia_semana]
        clima = clima_dict.get(fecha_str)

        if fecha_dt.weekday() >= 5 and dif_pct > 0:
            factor = "finde_semana"
            razon = f"fin de semana ({dia_nombre})"
        elif clima and clima.es_feriado and dif_pct > 0:
            factor = "feriado"
            razon = "feriado"
        elif clima and clima.condicion in ("Nublado", "Lluvia") and dif_pct < 0:
            factor = "clima"
            razon = f"clima {clima.condicion.lower()}"
        else:
            factor = "tendencia"
            razon = "tendencia de consumo"

        tipo = "aumentar" if dif_pct > 0 else "reducir"
        msg = (
            f"{'📈' if dif_pct > 0 else '📉'} {prod_nombre} — "
            f"{'+' if dif_pct > 0 else ''}{dif_pct}% para {dia_nombre} por {razon}. "
            f"{'Aumente' if dif_pct > 0 else 'Reduzca'} producción a {pred.demanda_estimada:.0f} uds."
        )

        recomendaciones.append({
            "tipo": tipo,
            "producto": prod_nombre,
            "fecha": fecha_str,
            "dia_semana": dia_nombre,
            "mensaje": msg,
            "factor": factor,
            "diferencia_pct": int(dif_pct),
            "demanda_estimada": pred.demanda_estimada,
        })

    recomendaciones.sort(key=lambda r: (r["fecha"], abs(r["diferencia_pct"])), reverse=True)

    return {
        "fecha_generacion": str(hoy),
        "recomendaciones": recomendaciones,
    }


# ── Dashboard KPIs ────────────────────────────────────────────────────────────

@app.get("/dashboard/resumen")
def dashboard_resumen(db: Session = Depends(get_db)):
    """KPIs principales para el tablero Streamlit en tiempo real."""
    hoy = date.today()
    ayer = hoy - timedelta(days=1)

    # Ventas hoy
    ventas_hoy = db.query(func.sum(models.FactVenta.cantidad_vendida)).filter(
        models.FactVenta.fecha == hoy
    ).scalar() or 0

    # Ventas ayer (para comparar)
    ventas_ayer = db.query(func.sum(models.FactVenta.cantidad_vendida)).filter(
        models.FactVenta.fecha == ayer
    ).scalar() or 0

    # Mermas hoy
    mermas_hoy = db.query(func.sum(models.FactMerma.cantidad_merma)).filter(
        models.FactMerma.fecha == hoy
    ).scalar() or 0

    # Mermas últimos 30 días
    desde_30 = hoy - timedelta(days=30)
    mermas_30d = db.query(func.sum(models.FactMerma.cantidad_merma)).filter(
        models.FactMerma.fecha >= desde_30
    ).scalar() or 0

    ventas_30d = db.query(func.sum(models.FactVenta.cantidad_vendida)).filter(
        models.FactVenta.fecha >= desde_30
    ).scalar() or 1

    pct_merma_30d = round((mermas_30d / (ventas_30d + mermas_30d)) * 100, 2)

    # Ventas últimos 7 días
    desde_7 = hoy - timedelta(days=7)
    ventas_7d = db.query(func.sum(models.FactVenta.cantidad_vendida)).filter(
        models.FactVenta.fecha >= desde_7
    ).scalar() or 0

    # Alertas de insumos
    insumos_criticos = db.query(models.InsumoCritico).filter(
        models.InsumoCritico.stock_actual < models.InsumoCritico.stock_minimo
    ).count()

    # Predicciones próximos 7 días
    predicciones_prox = db.query(
        models.DimProducto.nombre,
        func.sum(models.FactPrediccion.demanda_estimada).label("total"),
    ).join(models.DimProducto).filter(
        models.FactPrediccion.fecha_proyectada > hoy,
        models.FactPrediccion.fecha_proyectada <= hoy + timedelta(days=7),
    ).group_by(models.DimProducto.nombre).all()

    # Órdenes pendientes
    ordenes_pendientes = db.query(models.OrdenCompra).filter(
        models.OrdenCompra.estado == "pendiente"
    ).count()

    return {
        "fecha": str(hoy),
        "ventas_hoy": float(ventas_hoy),
        "ventas_ayer": float(ventas_ayer),
        "ventas_7d": float(ventas_7d),
        "mermas_hoy": float(mermas_hoy),
        "mermas_30d": float(mermas_30d),
        "pct_merma_30d": pct_merma_30d,
        "insumos_bajo_stock": insumos_criticos,
        "ordenes_pendientes": ordenes_pendientes,
        "prediccion_semana": [
            {"producto": r.nombre, "demanda_total_7d": float(r.total)}
            for r in predicciones_prox
        ],
    }


@app.get("/alertas/sobreproduccion")
def alertas_sobreproduccion(dias: int = 7, umbral: float = 10.0, db: Session = Depends(get_db)):
    """Detecta productos con sobreproducción recurrente (merma > umbral% en los últimos N días)."""
    hoy = date.today()
    desde = hoy - timedelta(days=dias)

    # Merma por motivo "Sobreproducción" por producto
    merma_sobreprod = db.query(
        models.FactMerma.producto_id,
        func.sum(models.FactMerma.cantidad_merma).label("total_merma"),
        func.count(models.FactMerma.id).label("frecuencia"),
    ).filter(
        models.FactMerma.fecha >= desde,
        models.FactMerma.motivo == "Sobreproducción",
    ).group_by(models.FactMerma.producto_id).all()

    # Ventas del mismo período por producto
    ventas_periodo = db.query(
        models.FactVenta.producto_id,
        func.sum(models.FactVenta.cantidad_vendida).label("total_ventas"),
    ).filter(models.FactVenta.fecha >= desde).group_by(models.FactVenta.producto_id).all()
    ventas_dict = {v.producto_id: float(v.total_ventas) for v in ventas_periodo}

    alertas = []
    for r in merma_sobreprod:
        ventas = ventas_dict.get(r.producto_id, 0) or 1
        total_merma = float(r.total_merma)
        tasa = round(total_merma / (ventas + total_merma) * 100, 1)
        if tasa >= umbral:
            prod = db.query(models.DimProducto).filter(models.DimProducto.id == r.producto_id).first()
            reduccion = round(tasa - umbral, 1)
            alertas.append({
                "producto_id": r.producto_id,
                "producto_nombre": prod.nombre if prod else f"ID {r.producto_id}",
                "tasa_sobreproduccion_pct": tasa,
                "unidades_perdidas": total_merma,
                "frecuencia": r.frecuencia,
                "reduccion_sugerida_pct": reduccion,
            })

    alertas.sort(key=lambda a: a["tasa_sobreproduccion_pct"], reverse=True)

    return {
        "total_alertas": len(alertas),
        "periodo_dias": dias,
        "umbral_pct": umbral,
        "alertas": alertas,
    }


@app.get("/dashboard/eficiencia")
def eficiencia_produccion(dias: int = 30, db: Session = Depends(get_db)):
    """Producción vs Ventas vs Merma por día y por producto, con ratio de eficiencia."""
    hoy = date.today()
    desde = hoy - timedelta(days=dias)

    # Producción por día
    prod_diario = db.query(
        models.FactProduccion.fecha,
        func.sum(models.FactProduccion.cantidad_producida).label("total"),
    ).filter(models.FactProduccion.fecha >= desde).group_by(
        models.FactProduccion.fecha
    ).order_by(models.FactProduccion.fecha).all()
    prod_dict = {str(r.fecha): float(r.total) for r in prod_diario}

    # Ventas por día
    ventas_diario = db.query(
        models.FactVenta.fecha,
        func.sum(models.FactVenta.cantidad_vendida).label("total"),
    ).filter(models.FactVenta.fecha >= desde).group_by(
        models.FactVenta.fecha
    ).order_by(models.FactVenta.fecha).all()
    ventas_dict = {str(r.fecha): float(r.total) for r in ventas_diario}

    # Mermas por día
    mermas_diario = db.query(
        models.FactMerma.fecha,
        func.sum(models.FactMerma.cantidad_merma).label("total"),
    ).filter(models.FactMerma.fecha >= desde).group_by(
        models.FactMerma.fecha
    ).order_by(models.FactMerma.fecha).all()
    mermas_dict = {str(r.fecha): float(r.total) for r in mermas_diario}

    # Ensamblar días
    todas_fechas = sorted(set(list(prod_dict.keys()) + list(ventas_dict.keys()) + list(mermas_dict.keys())))
    diario = []
    for f in todas_fechas:
        p = prod_dict.get(f, 0)
        v = ventas_dict.get(f, 0)
        m = mermas_dict.get(f, 0)
        diario.append({
            "fecha": f,
            "producido": p,
            "vendido": v,
            "merma": m,
            "eficiencia_pct": round(v / p * 100, 1) if p > 0 else 0,
        })

    # Totales globales
    total_prod = sum(d["producido"] for d in diario)
    total_vend = sum(d["vendido"] for d in diario)
    total_merm = sum(d["merma"] for d in diario)

    # Por producto (acumulado)
    por_producto = db.query(
        models.DimProducto.nombre.label("producto"),
        func.sum(models.FactVenta.cantidad_vendida).label("vendido"),
        models.DimProducto.costo,
    ).join(models.DimProducto).filter(
        models.FactVenta.fecha >= desde
    ).group_by(models.DimProducto.nombre, models.DimProducto.costo).all()

    prod_por_prod = db.query(
        models.DimProducto.nombre.label("producto"),
        func.sum(models.FactProduccion.cantidad_producida).label("producido"),
    ).join(models.DimProducto).filter(
        models.FactProduccion.fecha >= desde
    ).group_by(models.DimProducto.nombre).all()
    prod_pp_dict = {r.producto: float(r.producido) for r in prod_por_prod}

    merma_por_prod = db.query(
        models.DimProducto.nombre.label("producto"),
        func.sum(models.FactMerma.cantidad_merma).label("merma"),
    ).join(models.DimProducto).filter(
        models.FactMerma.fecha >= desde
    ).group_by(models.DimProducto.nombre).all()
    merma_pp_dict = {r.producto: float(r.merma) for r in merma_por_prod}

    resumen_productos = []
    for r in por_producto:
        p = prod_pp_dict.get(r.producto, 0)
        v = float(r.vendido)
        m = merma_pp_dict.get(r.producto, 0)
        resumen_productos.append({
            "producto": r.producto,
            "producido": p,
            "vendido": v,
            "merma": m,
            "eficiencia_pct": round(v / p * 100, 1) if p > 0 else 0,
            "perdida_economica": round(m * float(r.costo), 2),
        })

    resumen_productos.sort(key=lambda x: x["eficiencia_pct"])

    return {
        "periodo_dias": dias,
        "global": {
            "total_producido": total_prod,
            "total_vendido": total_vend,
            "total_merma": total_merm,
            "eficiencia_pct": round(total_vend / total_prod * 100, 1) if total_prod > 0 else 0,
        },
        "diario": diario,
        "por_producto": resumen_productos,
    }


# ── ML: Entrenar y Seed ───────────────────────────────────────────────────────

@app.post("/ml/entrenar")
def entrenar_modelos():
    """OE2: Lanza el entrenamiento del Random Forest para todos los productos."""
    try:
        from ml.trainer import entrenar_todos
        resultado = entrenar_todos()
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en entrenamiento: {str(e)}")

@app.post("/datos/semilla")
def cargar_datos_semilla():
    """Carga datos históricos sintéticos (365 días) para poder entrenar el modelo."""
    try:
        from ml.seed_data import run_seed
        resultado = run_seed()
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en seed: {str(e)}")

@app.post("/datos/completar")
def completar_datos():
    """Genera datos sintéticos para productos nuevos que tienen < 30 registros."""
    try:
        from ml.seed_data import completar_datos_faltantes
        resultado = completar_datos_faltantes()
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al completar datos: {str(e)}")

# ── ML: Metricas reales de modelos ────────────────────────────────────────────

@app.get("/ml/metricas")
def obtener_metricas_modelos():
    """Retorna las metricas reales (R2, MAE, RMSE) del MEJOR modelo entrenado."""
    import json, os
    from ml.trainer import MODELS_DIR
    db = SessionLocal()
    try:
        productos = db.query(models.DimProducto.id, models.DimProducto.nombre).all()
        metricas = []

        # Intentar best_model primero, luego legacy
        for prod_id, prod_nombre in productos:
            best_meta = os.path.join(MODELS_DIR, f"best_{prod_id}_meta.json")
            legacy_meta = os.path.join(MODELS_DIR, f"{prod_id}_meta.json")

            if os.path.exists(best_meta):
                with open(best_meta) as f:
                    meta = json.load(f)
                metricas.append({
                    "producto_id": prod_id, "producto_nombre": prod_nombre,
                    "r2": meta.get("r2"), "mae": meta.get("mae"),
                    "rmse": meta.get("rmse"), "modelo_disponible": True,
                    "mejor_algoritmo": meta.get("mejor_algoritmo", "Random Forest"),
                    "todos_resultados": meta.get("todos_resultados", []),
                })
            elif os.path.exists(legacy_meta):
                with open(legacy_meta) as f:
                    meta = json.load(f)
                metricas.append({
                    "producto_id": prod_id, "producto_nombre": prod_nombre,
                    "r2": meta.get("r2"), "mae": meta.get("mae"),
                    "rmse": meta.get("rmse"), "modelo_disponible": True,
                    "mejor_algoritmo": meta.get("algoritmo", "Random Forest (legacy)"),
                    "todos_resultados": [],
                })
            else:
                metricas.append({
                    "producto_id": prod_id, "producto_nombre": prod_nombre,
                    "r2": None, "mae": None, "rmse": None, "modelo_disponible": False,
                    "mejor_algoritmo": None, "todos_resultados": [],
                })

        return {"modelos": metricas}
    finally:
        db.close()


@app.post("/ml/comparar")
def comparar_modelos():
    """OE6: Entrena y compara TODOS los 7 modelos por producto.
    Retorna ranking detallado con el mejor modelo para cada producto."""
    try:
        from ml.comparador import entrenar_y_comparar_todos
        resultado = entrenar_y_comparar_todos()
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en comparación: {str(e)}")


@app.get("/ml/mejores-modelos")
def obtener_mejores_modelos():
    """Retorna el mapeo producto → mejor algoritmo desde best_model.json."""
    import json, os
    from ml.trainer import MODELS_DIR
    path = os.path.join(MODELS_DIR, "best_model.json")
    if not os.path.exists(path):
        return {"mejores_modelos": {}, "mensaje": "Ejecuta /ml/comparar primero"}
    with open(path) as f:
        mejores = json.load(f)
    return {"mejores_modelos": mejores}


# ── Clima: Sincronizacion con API externa ─────────────────────────────────────

@app.post("/clima/sincronizar")
async def sincronizar_clima_real(dias: int = 7):
    """
    Obtiene el pronostico real de Open-Meteo para Pacasmayo y lo guarda en dim_clima.
    UPSERT: actualiza si ya existe la fecha, inserta si no.
    """
    from ml.weather_api import obtener_pronostico_pacasmayo
    pronosticos = await obtener_pronostico_pacasmayo(dias)
    if not pronosticos:
        raise HTTPException(status_code=503, detail="No se pudo conectar a la API de clima.")
    db = SessionLocal()
    try:
        insertados, actualizados = 0, 0
        for p in pronosticos:
            existente = db.query(models.DimClima).filter(
                models.DimClima.fecha == p["fecha"]
            ).first()
            if existente:
                existente.temperatura_promedio = p["temperatura_promedio"]
                existente.condicion = p["condicion"]
                actualizados += 1
            else:
                db.add(models.DimClima(
                    fecha=p["fecha"], temperatura_promedio=p["temperatura_promedio"],
                    condicion=p["condicion"], es_feriado=False, evento_especial=None,
                ))
                insertados += 1
        db.commit()
        return {
            "status": "ok",
            "fuente": "Open-Meteo API (Pacasmayo, Lat=-7.4006, Lon=-79.5714)",
            "registros_insertados": insertados,
            "registros_actualizados": actualizados,
            "datos": pronosticos,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al guardar clima: {str(e)}")
    finally:
        db.close()


# ── Estado general del sistema ────────────────────────────────────────────────

@app.get("/sistema/estado")
def estado_sistema():
    """
    Health check completo: conectividad BD, estado de modelos ML,
    conteos de datos y URLs de todos los servicios del proyecto.
    """
    import json, os
    from ml.trainer import MODELS_DIR
    db = SessionLocal()
    try:
        n_p     = db.query(models.DimProducto).count()
        n_v     = db.query(models.FactVenta).count()
        n_m     = db.query(models.FactMerma).count()
        n_c     = db.query(models.DimClima).count()
        n_pred  = db.query(models.FactPrediccion).count()
        n_i     = db.query(models.InsumoCritico).count()
        n_prov  = db.query(models.Proveedor).count()
        n_ord   = db.query(models.OrdenCompra).count()
        n_alert = db.query(models.InsumoCritico).filter(
            models.InsumoCritico.stock_actual < models.InsumoCritico.stock_minimo
        ).count()

        productos = db.query(models.DimProducto.id, models.DimProducto.nombre).all()
        info_ml, listos = [], 0
        for pid, nombre in productos:
            best_pkl = os.path.join(MODELS_DIR, f"best_{pid}.pkl")
            legacy_pkl = os.path.join(MODELS_DIR, f"{pid}.pkl")
            tiene = os.path.exists(best_pkl) or os.path.exists(legacy_pkl)
            r2 = None
            algoritmo = None
            meta_p = os.path.join(MODELS_DIR, f"best_{pid}_meta.json")
            if os.path.exists(meta_p):
                with open(meta_p) as f:
                    d = json.load(f)
                    r2 = d.get("r2")
                    algoritmo = d.get("mejor_algoritmo")
            else:
                meta_legacy = os.path.join(MODELS_DIR, f"{pid}_meta.json")
                if os.path.exists(meta_legacy):
                    with open(meta_legacy) as f:
                        r2 = json.load(f).get("r2")
                        algoritmo = "Random Forest"
            if tiene:
                listos += 1
            info_ml.append({"producto": nombre, "entrenado": tiene, "r2": r2, "algoritmo": algoritmo})

        return {
            "status": "ok",
            "base_de_datos": {
                "conectada": True,
                "productos": n_p, "ventas": n_v, "mermas": n_m,
                "dias_clima": n_c, "predicciones": n_pred,
                "insumos": n_i, "alertas_stock": n_alert,
                "proveedores": n_prov, "ordenes_compra": n_ord,
            },
            "machine_learning": {
                "modelos_listos": listos,
                "total_productos": len(productos),
                "todos_entrenados": listos == len(productos),
                "detalle": info_ml,
            },
            "servicios": {
                "api":       "http://localhost:8000",
                "docs":      "http://localhost:8000/docs",
                "pgadmin":   "http://localhost:8080",
                "n8n":       "http://localhost:5678",
                "streamlit": "http://localhost:8501",
                "clima_api": "Open-Meteo (sin API key)",
            },
        }
    except Exception as e:
        return {"status": "error", "detalle": str(e)}
    finally:
        db.close()

if False:
    @app.delete("/mermas/{merma_id}")
    def eliminar_merma(merma_id: int, db: Session = Depends(get_db)):
        """Elimina un registro de merma."""
        merma = db.query(models.FactMerma).filter(models.FactMerma.id == merma_id).first()
        if not merma:
            raise HTTPException(status_code=404, detail="Merma no encontrada")
        db.delete(merma)
        db.commit()
        return {"mensaje": f"Merma {merma_id} eliminada"}


# ── Chatbot IA ─────────────────────────────────────────────────────────────────

class ChatbotPregunta(BaseModel):
    pregunta: str

def _obtener_datos_sistema(db: Session):
    """Reúne los datos actuales del sistema para contexto del chatbot."""
    hoy = date.today()
    desde_7 = hoy - timedelta(days=7)
    desde_30 = hoy - timedelta(days=30)

    ventas_7d = db.query(func.sum(models.FactVenta.cantidad_vendida)).filter(
        models.FactVenta.fecha >= desde_7
    ).scalar() or 0

    ventas_30d = db.query(func.sum(models.FactVenta.cantidad_vendida)).filter(
        models.FactVenta.fecha >= desde_30
    ).scalar() or 0

    mermas_30d = db.query(func.sum(models.FactMerma.cantidad_merma)).filter(
        models.FactMerma.fecha >= desde_30
    ).scalar() or 0

    pct_merma = round((mermas_30d / (ventas_30d + mermas_30d)) * 100, 2) if (ventas_30d + mermas_30d) > 0 else 0

    productos = db.query(models.DimProducto).all()
    n_productos = len(productos)

    insumos_bajos = db.query(models.InsumoCritico).filter(
        models.InsumoCritico.stock_actual < models.InsumoCritico.stock_minimo
    ).all()

    alertas = [{"nombre": i.nombre, "stock": i.stock_actual, "minimo": i.stock_minimo, "unidad": i.unidad_medida} for i in insumos_bajos]

    productos_top = db.query(
        models.DimProducto.nombre,
        func.sum(models.FactVenta.cantidad_vendida).label("total")
    ).join(models.FactVenta).filter(
        models.FactVenta.fecha >= desde_7
    ).group_by(models.DimProducto.nombre).order_by(func.sum(models.FactVenta.cantidad_vendida).desc()).limit(5).all()

    ordenes_pendientes = db.query(models.OrdenCompra).filter(
        models.OrdenCompra.estado == "pendiente"
    ).count()

    return {
        "ventas_7d": float(ventas_7d),
        "ventas_30d": float(ventas_30d),
        "mermas_30d": float(mermas_30d),
        "pct_merma": pct_merma,
        "n_productos": n_productos,
        "alertas_stock": alertas,
        "productos_top": [{"nombre": p.nombre, "ventas": float(p.total)} for p in productos_top],
        "ordenes_pendientes": ordenes_pendientes,
    }

def _generar_respuesta(pregunta: str, datos: dict) -> str:
    """Genera respuesta basada en palabras clave y datos reales."""
    pregunta_lower = pregunta.lower()
    resp = []

    if any(p in pregunta_lower for p in ["hola", "buenos", "buenas", "saludo", "que tal"]):
        return "¡Hola! Soy el asistente de Panadería Victoria. Puedo ayudarte con información sobre ventas, inventario, mermas, predicciones, productos y más. ¿Qué necesitas saber?"

    if any(p in pregunta_lower for p in ["venta", "vender", "vendido", "vendi"]):
        resp.append(f"📊 **Resumen de Ventas:**")
        resp.append(f"  • Últimos 7 días: **{datos['ventas_7d']} unidades**")
        resp.append(f"  • Últimos 30 días: **{datos['ventas_30d']} unidades**")
        if datos['productos_top']:
            resp.append(f"\n🏆 **Productos más vendidos (últimos 7 días):**")
            for i, p in enumerate(datos['productos_top'][:3], 1):
                resp.append(f"  {i}. {p['nombre']}: {p['ventas']} unidades")
        return "\n".join(resp)

    if any(p in pregunta_lower for p in ["stock", "inventario", "insumo", "material", "existencia"]):
        resp.append(f"📦 **Estado del Inventario:**")
        if datos['alertas_stock']:
            resp.append("\n⚠️ **Alertas de stock bajo:**")
            for a in datos['alertas_stock']:
                resp.append(f"  • {a['nombre']}: {a['stock']}/{a['minimo']} {a['unidad']}")
        else:
            resp.append("  ✅ No hay alertas de stock bajo.")
        return "\n".join(resp)

    if any(p in pregunta_lower for p in ["merma", "perder", "perdida", "desperdicio", "sobra"]):
        resp.append(f"📉 **Análisis de Mermas:**")
        resp.append(f"  • Últimos 30 días: **{datos['mermas_30d']} unidades perdidas**")
        resp.append(f"  • Porcentaje de merma: **{datos['pct_merma']}%**")
        if datos['pct_merma'] > 5:
            resp.append("\n⚠️ Recomendación: El porcentaje de merma está alto. Considera reducir producción o mejorar la planificación.")
        else:
            resp.append("\n✅ Las mermas están dentro de un rango saludable (menos del 5%).")
        return "\n".join(resp)

    if any(p in pregunta_lower for p in ["producto", "catalogo", "menu", "articulo"]):
        resp.append(f"🍞 **Catálogo de Productos:**")
        resp.append(f"  • Total de productos: **{datos['n_productos']}**")
        if datos['productos_top']:
            resp.append(f"\n🔥 **Top productos en ventas:**")
            for p in datos['productos_top'][:3]:
                resp.append(f"  • {p['nombre']}: {p['ventas']} unidades")
        return "\n".join(resp)

    if any(p in pregunta_lower for p in ["orden", "compra", "pedido", "proveedor"]):
        resp.append(f"🛒 **Órdenes de Compra:**")
        resp.append(f"  • Pendientes: **{datos['ordenes_pendientes']}**")
        if datos['ordenes_pendientes'] > 0:
            resp.append("\n💡 Ve a 'Órdenes de Compra' para ver los detalles.")
        return "\n".join(resp)

    if any(p in pregunta_lower for p in ["predic", "pronostic", "previs", "futuro", "siguiente"]):
        resp.append("🔮 **Sistema de Predicciones:**")
        resp.append("El sistema usa Machine Learning (Random Forest) para predecir la demanda basándose en:")
        resp.append("  • Datos históricos de ventas")
        resp.append("  • Clima y condiciones meteorológicas")
        resp.append("  • Día de la semana y eventos especiales")
        resp.append("\n💡 Ve a la página 'Predicciones' para ver los próximos 7 días.")
        return "\n".join(resp)

    if any(p in pregunta_lower for p in ["ayuda", "como", "qué puedo", "que puedo", "instruc"]):
        return """📖 **Puedo ayudarte con:**

• **Ventas**: "Cómo van las ventas?", "ventas de esta semana"
• **Inventario**: "Qué insumos hay?", "stock de harina"
• **Mermas**: "Cuántas mermas hay?", "porcentaje de merma"
• **Productos**: "Qué productos tengo?", "top ventas"
• **Órdenes**: "Tengo órdenes pendientes?"
• **Predicciones**: "Qué se predice para mañana?"
• **General**: "Dame un resumen del sistema"

¿En qué puedo ayudarte?"""

    return f"""🤖 Gracias por tu pregunta: "{pregunta}"

Tengo estos datos del sistema:
• Ventas 7 días: {datos['ventas_7d']} unidades
• Ventas 30 días: {datos['ventas_30d']} unidades  
• Mermas 30 días: {datos['mermas_30d']} unidades ({datos['pct_merma']}%)
• Productos: {datos['n_productos']}
• Alertas de stock: {len(datos['alertas_stock'])}
• Órdenes pendientes: {datos['ordenes_pendientes']}

¿Puedes ser más específico? Puedo ayudarte con ventas, inventario, mermas, productos, predicciones y más."""


@app.post("/chatbot/pregunta")
def chatbot_pregunta(pregunta: ChatbotPregunta, db: Session = Depends(get_db)):
    """Endpoint para el chatbot: recibe pregunta y retorna respuesta basada en datos."""
    datos = _obtener_datos_sistema(db)
    respuesta = _generar_respuesta(pregunta.pregunta, datos)
    return {"respuesta": datos, "mensaje": respuesta}


# ── Reportes Financieros ────────────────────────────────────────────────────────

class ReporteRequest(BaseModel):
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None

@app.post("/reportes/estado-resultados")
def estado_resultados(reporte: ReporteRequest, db: Session = Depends(get_db)):
    """Genera estado de resultados con ingresos, costos y ganancia."""
    desde = reporte.fecha_inicio or (date.today() - timedelta(days=30))
    hasta = reporte.fecha_fin or date.today()
    
    # Calcular ventas totales agrupadas por producto
    ventas = db.query(
        models.FactVenta.producto_id,
        func.sum(models.FactVenta.cantidad_vendida).label("total_cantidad")
    ).filter(
        models.FactVenta.fecha >= desde,
        models.FactVenta.fecha <= hasta
    ).group_by(models.FactVenta.producto_id).all()
    
    productos = {p.id: p for p in db.query(models.DimProducto).all()}
    
    ingresos = 0
    costos = 0
    detalle_ventas = []
    
    for v in ventas:
        prod = productos.get(v.producto_id)
        if prod:
            cantidad = float(v.total_cantidad)
            ingreso = cantidad * prod.precio
            costo = cantidad * prod.costo
            ingresos += ingreso
            costos += costo
            detalle_ventas.append({
                "producto": prod.nombre,
                "categoria": prod.categoria,
                "cantidad": cantidad,
                "precio": prod.precio,
                "costo_unitario": prod.costo,
                "ingreso": round(ingreso, 2),
                "costo": round(costo, 2),
                "ganancia": round(ingreso - costo, 2)
            })
    
    # Ordenar por ganancia descendente
    detalle_ventas.sort(key=lambda x: x['ganancia'], reverse=True)
    
    ganancia_neta = ingresos - costos
    margen = (ganancia_neta / ingresos * 100) if ingresos > 0 else 0
    
    return {
        "periodo": {"inicio": str(desde), "fin": str(hasta)},
        "ingresos": round(ingresos, 2),
        "costos": round(costos, 2),
        "ganancia_neta": round(ganancia_neta, 2),
        "margen_porcentaje": round(margen, 2),
        "detalle": detalle_ventas
    }

@app.get("/reportes/ventas-diarias")
def ventas_diarias(fecha_inicio: str = None, fecha_fin: str = None, db: Session = Depends(get_db)):
    """Retorna ventas diarias para gráficos."""
    desde = date.fromisoformat(fecha_inicio) if fecha_inicio else (date.today() - timedelta(days=30))
    hasta = date.fromisoformat(fecha_fin) if fecha_fin else date.today()
    
    ventas = db.query(
        models.FactVenta.fecha,
        func.sum(models.FactVenta.cantidad_vendida).label("unidades"),
        func.count(models.FactVenta.id).label("transacciones")
    ).filter(
        models.FactVenta.fecha >= desde,
        models.FactVenta.fecha <= hasta
    ).group_by(models.FactVenta.fecha).order_by(models.FactVenta.fecha).all()
    
    return {
        "fechas": [str(v.fecha) for v in ventas],
        "unidades": [float(v.unidades) for v in ventas],
        "transacciones": [v.transacciones for v in ventas]
    }

@app.get("/reportes/productos-rentabilidad")
def productos_rentabilidad(db: Session = Depends(get_db)):
    """Retorna rentabilidad por producto."""
    productos = db.query(models.DimProducto).all()
    
    resultado = []
    for prod in productos:
        ventas = db.query(
            func.sum(models.FactVenta.cantidad_vendida).label("total_vendido")
        ).filter(models.FactVenta.producto_id == prod.id).scalar() or 0
        
        ingreso = ventas * prod.precio
        costo = ventas * prod.costo
        ganancia = ingreso - costo
        
        resultado.append({
            "producto": prod.nombre,
            "categoria": prod.categoria,
            "unidades_vendidas": float(ventas),
            "precio": prod.precio,
            "costo": prod.costo,
            "ingreso": float(ingreso),
            "costo_total": float(costo),
            "ganancia": float(ganancia),
            "margen": float((ganancia / ingreso * 100) if ingreso > 0 else 0)
        })
    
    resultado.sort(key=lambda x: x['ganancia'], reverse=True)
    return resultado

@app.get("/reportes/productos-porcentaje")
def productos_porcentaje(fecha_inicio: str = None, fecha_fin: str = None, db: Session = Depends(get_db)):
    """Retorna porcentaje de ventas por producto."""
    desde = date.fromisoformat(fecha_inicio) if fecha_inicio else (date.today() - timedelta(days=30))
    hasta = date.fromisoformat(fecha_fin) if fecha_fin else date.today()
    
    ventas = db.query(
        models.FactVenta.producto_id,
        func.sum(models.FactVenta.cantidad_vendida).label("total")
    ).filter(
        models.FactVenta.fecha >= desde,
        models.FactVenta.fecha <= hasta
    ).group_by(models.FactVenta.producto_id).all()
    
    productos = {p.id: p.nombre for p in db.query(models.DimProducto).all()}
    
    total = sum(float(v.total) for v in ventas)
    
    resultado = []
    for v in ventas:
        porcentaje = (float(v.total) / total * 100) if total > 0 else 0
        resultado.append({
            "producto": productos.get(v.producto_id, f"Producto {v.producto_id}"),
            "unidades": float(v.total),
            "porcentaje": round(porcentaje, 2)
        })
    
    resultado.sort(key=lambda x: x['unidades'], reverse=True)
    return resultado
