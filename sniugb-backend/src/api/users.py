from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from src.utils.security import get_current_user, get_db, verify_password, get_password_hash
from src.models.database_models import Usuario
from src.models.user_models import UserResponseSchema, UserUpdateProfileSchema, UserUpdatePasswordSchema

users_router = APIRouter(
    prefix="/users",
    tags=["Usuarios"],
    route_class=APIRoute
)

@users_router.get("/me", response_model=UserResponseSchema)
async def read_users_me(current_user: Usuario = Depends(get_current_user)):
    """
    Obtiene el perfil del usuario actualmente autenticado.
    """
    return current_user

@users_router.put("/me", response_model=UserResponseSchema)
async def update_user_profile(
    user_data: UserUpdateProfileSchema, 
    current_user: Usuario = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Actualiza los datos de contacto (teléfono, email) del usuario autenticado.
    El DNI y el nombre no son modificables.
    """
    if user_data.email:
        current_user.email = user_data.email
    if user_data.telefono:
        current_user.telefono = user_data.telefono
    
    try:
        db.commit()
        db.refresh(current_user)
        return current_user
    except Exception as e:
        db.rollback()
        # Manejar error de email duplicado si es necesario
        if "Key (email)" in str(e):
             raise HTTPException(status_code=400, detail="El correo electrónico ya está en uso por otra cuenta.")
        raise HTTPException(status_code=500, detail="No se pudo actualizar el perfil.")

@users_router.put("/me/password")
async def update_user_password(
    password_data: UserUpdatePasswordSchema,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza la contraseña del usuario autenticado.
    Requiere la contraseña actual para verificación.
    """
    # 1. Verificar que la contraseña actual es correcta
    if not verify_password(password_data.current_password, current_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La contraseña actual es incorrecta.")
        
    # 2. Encriptar la nueva contraseña
    new_hashed_password = get_password_hash(password_data.new_password)
    
    # 3. Actualizar en la base de datos
    current_user.password = new_hashed_password
    db.commit()
    
    return {"message": "Contraseña actualizada exitosamente."}