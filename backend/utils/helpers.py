"""
helpers.py - Funciones y constantes de utilidad para el backend.
"""
import base64
import io
import pyotp
import qrcode
from fastapi import HTTPException
from datetime import datetime

# ---------------------------------------------------------------------------
# Usuarios fijos (admin / gerente) – no viven en la BD
# ---------------------------------------------------------------------------
FIJOS = {
    "admin": {"rol": "administrador", "vendedor_id": None},
    "gerente": {"rol": "gerente", "vendedor_id": None},
    "cocina": {"rol": "cocina", "vendedor_id": None},
}

# Mapa rápido username -> rol para los usuarios fijos
FIJOS_ROL = {k: v["rol"] for k, v in FIJOS.items()}


# ---------------------------------------------------------------------------
# Helpers de base de datos
# ---------------------------------------------------------------------------
def get_or_404(db, model, pk, detail="No encontrado"):
    """Busca un registro por PK o lanza 404."""
    obj = db.query(model).filter(model.id == pk).first()
    if not obj:
        raise HTTPException(status_code=404, detail=detail)
    return obj


# ---------------------------------------------------------------------------
# Helpers de métricas
# ---------------------------------------------------------------------------
def calcular_tasa_merma(total_ventas: float, total_merma: float, precision: int = 2) -> float:
    """Calcula el porcentaje de merma sobre las ventas."""
    if not total_ventas or total_ventas == 0:
        return 0.0
    return round((total_merma / total_ventas) * 100, precision)


# ---------------------------------------------------------------------------
# Helpers de sesión
# ---------------------------------------------------------------------------
def validar_token_sesion(session_token: str, username: str, session_store: dict):
    """
    Valida que el session_token exista, no haya expirado y pertenezca al usuario.
    Lanza HTTPException 401 si falla alguna condición.
    """
    if session_token not in session_store:
        raise HTTPException(status_code=401, detail="Token de sesión inválido")
    data = session_store[session_token]
    if data.get("username") != username:
        raise HTTPException(status_code=401, detail="Token de sesión no coincide con el usuario")
    if datetime.now() > data.get("expira", datetime.min):
        del session_store[session_token]
        raise HTTPException(status_code=401, detail="Token de sesión expirado")
    return data


# ---------------------------------------------------------------------------
# Helpers de 2FA / QR
# ---------------------------------------------------------------------------
def _generar_qr_base64(uri: str) -> str:
    """Genera un QR como imagen PNG en base64 a partir de un URI."""
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def generar_qr_2fa(username: str, issuer: str = "Panaderia Victoria") -> dict:
    """
    Genera un nuevo secreto TOTP y devuelve el QR en base64.
    Retorna: { "totp_secret": str, "qr_base64": str }
    """
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=username, issuer_name=issuer)
    qr_b64 = _generar_qr_base64(uri)
    return {"totp_secret": secret, "qr_base64": qr_b64}


def generar_qr_desde_secret(secret: str, username: str, issuer: str = "Panaderia Victoria") -> dict:
    """
    Regenera el QR a partir de un secreto TOTP ya existente.
    Retorna: { "qr_base64": str }
    """
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=username, issuer_name=issuer)
    qr_b64 = _generar_qr_base64(uri)
    return {"qr_base64": qr_b64}
