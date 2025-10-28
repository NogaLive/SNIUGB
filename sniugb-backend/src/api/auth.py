from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.routing import APIRoute
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import os

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
    get_current_user,  # para logout
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
    Autentica a un usuario y devuelve access_token, refresh_token y rol.
    """
    user = db.query(Usuario).filter(Usuario.numero_de_dni == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="DNI o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Access
    access_token = create_access_token(data={"sub": user.numero_de_dni, "rol": user.rol.value})

    # Refresh (compatibilidad con 2 firmas: (token, jti, exp) ó solo token)
    rt = create_refresh_token(data={"sub": user.numero_de_dni, "rol": user.rol.value})
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
        "rol": user.rol.value,
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
    user = db.query(Usuario).filter(Usuario.numero_de_dni == body.numero_de_dni).first()

    # respuesta neutra para no filtrar usuarios
    if not user:
        return {"message": "Se envió un código a su método de recuperación."}

    code = str(random.randint(100000, 999999))
    user.reset_token = code
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()

    method = (body.method or "").lower()
    if method == "email":
        send_reset_code_by_email(user.email, code)
    elif method == "whatsapp":
        send_reset_code_by_whatsapp(user.telefono, code)
    else:
        raise HTTPException(status_code=400, detail="Método no válido. Debe ser 'email' o 'whatsapp'.")

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
    """
    user = db.query(Usuario).filter(Usuario.numero_de_dni == body.numero_de_dni).first()

    # Comprobación de seguridad robusta
    if (
        not user
        or not user.reset_token
        or user.reset_token != body.code
        or user.reset_token_expires < datetime.now(timezone.utc)
    ):
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
    user = db.query(Usuario).filter(Usuario.numero_de_dni == body.numero_de_dni).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if (
        not user.reset_token
        or user.reset_token != body.code
        or user.reset_token_expires < datetime.now(timezone.utc)
    ):
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

    # Modo persistente (si hay jti en el payload)
    if jti and exp:
        token_row = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
        now = datetime.now(timezone.utc)
        if not token_row or token_row.revoked_at is not None or token_row.expires_at < now:
            raise HTTPException(status_code=401, detail="Refresh no válido o revocado")

        # Revocar el refresh usado
        token_row.revoked_at = now

        # Emitir nuevos tokens
        access_token = create_access_token(data={"sub": user.numero_de_dni, "rol": user.rol.value})
        rt = create_refresh_token(data={"sub": user.numero_de_dni, "rol": user.rol.value})
        if isinstance(rt, tuple) and len(rt) == 3:
            new_refresh, new_jti, new_exp = rt
            db.add(RefreshToken(jti=new_jti, usuario_dni=user.numero_de_dni, expires_at=new_exp))
            db.commit()
            return {"access_token": access_token, "token_type": "bearer", "refresh_token": new_refresh, "rol": user.rol.value}
        else:
            # Si por algún motivo devuelve solo cadena, al menos devolvemos el access; no persistimos (stateless)
            new_refresh = rt
            db.commit()
            return {"access_token": access_token, "token_type": "bearer", "refresh_token": new_refresh, "rol": user.rol.value}

    # Modo stateless (sin jti en payload)
    access_token = create_access_token(data={"sub": user.numero_de_dni, "rol": user.rol.value})
    new_refresh = create_refresh_token(data={"sub": user.numero_de_dni, "rol": user.rol.value})
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": new_refresh, "rol": user.rol.value}


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
