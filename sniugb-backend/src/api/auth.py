from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.routing import APIRoute
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import random
from datetime import datetime, timedelta, timezone

# Importaciones de modelos y servicios
from src.models.user_models import UserCreateSchema, UserResponseSchema, ForgotPasswordSchema, VerifyCodeSchema, ResetPasswordSchema
from src.models.database_models import Usuario
from src.services.auth_service import create_new_user
from src.services.notification_service import send_reset_code_by_email, send_reset_code_by_whatsapp

# Importaciones de seguridad
from src.utils.security import verify_password, create_access_token, get_db, get_password_hash, validate_password

auth_router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"],
    route_class=APIRoute
)

@auth_router.post("/register", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreateSchema, db: Session = Depends(get_db)):

    if not validate_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña no cumple con los requisitos de seguridad."
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

@auth_router.post("/login")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Autentica a un usuario y devuelve un token de acceso junto con su rol.
    """
    user = db.query(Usuario).filter(Usuario.numero_de_dni == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="DNI o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Se incluye el rol en el payload del token para que esté disponible en cada petición
    access_token = create_access_token(data={"sub": user.numero_de_dni, "rol": user.rol.value})
    
    # Se devuelve el token y el rol para que el frontend sepa a dónde redirigir
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "rol": user.rol.value 
    }

@auth_router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordSchema, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.numero_de_dni == request.numero_de_dni).first()
    
    if not user:
        return {"message": "Se envió un código a su método de recuperación."}

    code = str(random.randint(100000, 999999))
    
    user.reset_token = code
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()

    if request.method.lower() == 'email':
        send_reset_code_by_email(user.email, code)
    elif request.method.lower() == 'whatsapp':
        send_reset_code_by_whatsapp(user.telefono, code)
    else:
        raise HTTPException(status_code=400, detail="Método no válido. Debe ser 'email' o 'whatsapp'.")
        
    return {"message": "Se envió un código a su método de recuperación."}

@auth_router.post("/verify-code")
async def verify_reset_code(request: VerifyCodeSchema, db: Session = Depends(get_db)):
    """
    Verifica si un código de reseteo es válido para un DNI.
    """
    user = db.query(Usuario).filter(Usuario.numero_de_dni == request.numero_de_dni).first()

    # Comprobación de seguridad robusta
    if not user or \
       not user.reset_token or \
       user.reset_token != request.code or \
       user.reset_token_expires < datetime.now(timezone.utc):
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código es inválido o ha expirado."
        )
    
    # Si el código es correcto y no ha expirado, devolvemos un éxito.
    return {"message": "Código verificado exitosamente."}

@auth_router.post("/reset-password")
async def reset_password(request: ResetPasswordSchema, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.numero_de_dni == request.numero_de_dni).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if not user.reset_token or user.reset_token != request.code or user.reset_token_expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="El código es inválido o ha expirado.")
        
    user.password = get_password_hash(request.new_password)
    
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    
    return {"message": "Contraseña actualizada exitosamente."}