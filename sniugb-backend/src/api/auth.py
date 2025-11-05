from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.routing import APIRoute
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import os
import secrets

from src.utils.limiter import limiter
from src.models.user_models import (
    UserCreateSchema,
    UserResponseSchema,
    ForgotPasswordSchema,
    VerifyCodeSchema,
    ResetPasswordSchema,
)
from src.models.database_models import Usuario, RefreshToken
from src.services.auth_service import create_new_user
from src.services.notification_service import (
    send_reset_code_by_email,
    send_reset_code_by_whatsapp,
)
from src.utils.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    get_db,
    get_password_hash,
    validate_password,
    get_current_user,
)

auth_router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"],
    route_class=APIRoute,
)

# ------------------------------
# Registro
# ------------------------------
@auth_router.post("/register", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreateSchema, db: Session = Depends(get_db)):
    if not validate_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña no cumple con los requisitos de seguridad.",
        )

    new_user = create_new_user(user_data, db)
    if new_user == "dni_not_found":
        raise HTTPException(status_code=404, detail="El DNI ingresado no es válido o no fue encontrado.")
    if new_user == "duplicate_phone":
        raise HTTPException(status_code=400, detail="El número de teléfono ya está registrado.")
    if new_user == "duplicate_entry":
        raise HTTPException(status_code=400, detail="El DNI o el correo electrónico ya están registrados.")
    if not new_user:
        raise HTTPException(status_code=500, detail="Ocurrió un error inesperado al crear el usuario.")
    return new_user


# ------------------------------
# Login
# ------------------------------
@auth_router.post("/login")
@limiter.limit("5/minute")
async def login_user(
    request: Request,  # requerido por SlowAPI
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Autentica a un usuario y devuelve access_token, refresh_token y rol (lowercase).
    """
    user = db.query(Usuario).filter(Usuario.numero_de_dni == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="DNI o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Access
    user_role_val = getattr(user.rol, "value", user.rol)
    role_lower = str(user_role_val).lower()

    access_token = create_access_token(data={"sub": user.numero_de_dni, "rol": role_lower})

    # Refresh (compatibilidad con 2 firmas: (token, jti, exp) ó solo token)
    rt = create_refresh_token(data={"sub": user.numero_de_dni, "rol": role_lower})
    refresh_token, jti, exp = None, None, None
    if isinstance(rt, tuple) and len(rt) == 3:
        refresh_token, jti, exp = rt
    else:
        refresh_token = rt  # modo stateless

    # Persistencia (si hay jti/exp -> modo con revocación)
    if jti and exp:
        db.add(RefreshToken(jti=jti, usuario_dni=user.numero_de_dni, expires_at=exp))
        db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "rol": role_lower,
    }


# ------------------------------
# Forgot password
# ------------------------------
@auth_router.post("/forgot-password")
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,  # requerido por SlowAPI
    body: ForgotPasswordSchema,
    db: Session = Depends(get_db),
):
    """
    Genera y envía un código de recuperación por email o WhatsApp.
    - No revela si el usuario existe (respuesta neutra si no existe).
    - Si el envío falla para un usuario válido, devuelve 500 para poder depurar.
    """
    user = db.query(Usuario).filter(Usuario.numero_de_dni == body.numero_de_dni).first()

    # Si NO existe, responder neutro para no filtrar usuarios.
    if not user:
        return {"message": "Se envió un código a su método de recuperación."}

    # Generar código (6 dígitos) y expiración (10 min)
    code = f"{secrets.randbelow(1_000_000):06d}"
    user.reset_token = code
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()

    method = (body.method or "").lower()
    sent_ok = False

    if method == "email":
        if not user.email:
            raise HTTPException(status_code=400, detail="El usuario no tiene email registrado.")
        sent_ok = send_reset_code_by_email(user.email, code)

    elif method == "whatsapp":
        if not user.telefono:
            raise HTTPException(status_code=400, detail="El usuario no tiene teléfono registrado.")
        sent_ok = send_reset_code_by_whatsapp(user.telefono, code)

    else:
        raise HTTPException(status_code=400, detail="Método no válido. Debe ser 'email' o 'whatsapp'.")

    # Si el canal de envío falla, informamos 500 para poder ver el problema en frontend y logs
    if not sent_ok:
        raise HTTPException(status_code=500, detail="No se pudo enviar el código. Revise la configuración del canal.")

    return {"message": "Se envió un código a su método de recuperación."}


# ------------------------------
# Verify code
# ------------------------------
@auth_router.post("/verify-code")
@limiter.limit("5/minute")
async def verify_reset_code(
    request: Request,  # requerido por SlowAPI
    body: VerifyCodeSchema,
    db: Session = Depends(get_db),
):
    """
    Verifica si un código de reseteo es válido para un DNI.
    Manejo robusto de tz naive/aware.
    """
    user = db.query(Usuario).filter(Usuario.numero_de_dni == body.numero_de_dni).first()

    if not user or not user.reset_token or not user.reset_token_expires:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código es inválido o ha expirado.")

    now = datetime.now(timezone.utc)
    expires = user.reset_token_expires
    # Normalizar naive -> aware (UTC)
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if user.reset_token != body.code or now > expires:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código es inválido o ha expirado.")

    return {"message": "Código verificado exitosamente."}


# ------------------------------
# Reset password
# ------------------------------
@auth_router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(
    request: Request,  # requerido por SlowAPI
    body: ResetPasswordSchema,
    db: Session = Depends(get_db),
):
    """
    Resetea la contraseña si el código es válido y no ha expirado.
    Manejo robusto de tz naive/aware.
    """
    user = db.query(Usuario).filter(Usuario.numero_de_dni == body.numero_de_dni).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if not user.reset_token or not user.reset_token_expires:
        raise HTTPException(status_code=400, detail="El código es inválido o ha expirado.")

    now = datetime.now(timezone.utc)
    expires = user.reset_token_expires
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if user.reset_token != body.code or now > expires:
        raise HTTPException(status_code=400, detail="El código es inválido o ha expirado.")

    user.password = get_password_hash(body.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {"message": "Contraseña actualizada exitosamente."}


# ------------------------------
# Refresh (con rotación si hay jti)
# ------------------------------
from pydantic import BaseModel
class RefreshRequest(BaseModel):
    refresh_token: str

@auth_router.post("/refresh")
async def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """
    Intercambia un refresh_token por un nuevo par (access + refresh).
    Si el refresh tiene jti (persistente), valida en DB y rota (revoca el anterior).
    """
    try:
        payload = jwt.decode(body.refresh_token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Token inválido")
        sub = payload.get("sub")
        jti = payload.get("jti")
        exp = payload.get("exp")
        if not sub:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    user = db.query(Usuario).filter(Usuario.numero_de_dni == sub).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    role_lower = str(getattr(user.rol, "value", user.rol)).lower()

    # Modo persistente (si hay jti en el payload)
    if jti and exp:
        token_row = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
        now = datetime.now(timezone.utc)
        if not token_row or token_row.revoked_at is not None or token_row.expires_at < now:
            raise HTTPException(status_code=401, detail="Refresh no válido o revocado")

        # Revocar el refresh usado
        token_row.revoked_at = now

        # Emitir nuevos tokens
        access_token = create_access_token(data={"sub": user.numero_de_dni, "rol": role_lower})
        rt = create_refresh_token(data={"sub": user.numero_de_dni, "rol": role_lower})
        if isinstance(rt, tuple) and len(rt) == 3:
            new_refresh, new_jti, new_exp = rt
            db.add(RefreshToken(jti=new_jti, usuario_dni=user.numero_de_dni, expires_at=new_exp))
            db.commit()
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "refresh_token": new_refresh,
                "rol": role_lower,
            }
        else:
            new_refresh = rt  # stateless fallback
            db.commit()
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "refresh_token": new_refresh,
                "rol": role_lower,
            }

    # Modo stateless (sin jti en payload)
    access_token = create_access_token(data={"sub": user.numero_de_dni, "rol": role_lower})
    new_refresh = create_refresh_token(data={"sub": user.numero_de_dni, "rol": role_lower})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh,
        "rol": role_lower,
    }


# ------------------------------
# Logout (revoca todos los refresh activos del usuario actual)
# ------------------------------
@auth_router.post("/logout", status_code=204)
async def logout(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Revoca todos los refresh tokens activos del usuario actual (modo persistente).
    En modo stateless, el cliente ignora el refresh localmente.
    """
    now = datetime.now(timezone.utc)
    tokens = (
        db.query(RefreshToken)
        .filter(RefreshToken.usuario_dni == current_user.numero_de_dni, RefreshToken.revoked_at.is_(None))
        .all()
    )
    for t in tokens:
        t.revoked_at = now
    db.commit()
    return None
