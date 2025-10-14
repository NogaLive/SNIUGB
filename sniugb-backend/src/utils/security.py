from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
import re

from sqlalchemy.orm import Session
from src.models.database_models import Usuario, UserRole
from src.config.database import SessionLocal

load_dotenv()

# --- Configuración de Seguridad ---
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440 # 24 horas

# --- Hashing de Contraseñas ---
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- Creación de Tokens JWT ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Dependencias de Seguridad (Guardianes) ---

def get_db():
    """Dependencia para obtener una sesión de la base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Usuario:
    """
    Decodifica el token, valida al usuario y devuelve el objeto de usuario completo.
    Protege rutas que requieren que un usuario simplemente esté logueado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        dni: str = payload.get("sub")
        if dni is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(Usuario).filter(Usuario.numero_de_dni == dni).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_admin_user(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """
    Una dependencia que se construye sobre get_current_user y verifica si el rol es 'ADMIN'.
    Protege las rutas exclusivas del panel de administración.
    """
    if current_user.rol != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requieren permisos de administrador."
        )
    return current_user

def validate_password(password: str) -> bool:
    """
    Valida la contraseña contra los requisitos del negocio:
    - 8 a 16 caracteres de longitud.
    - Al menos un número.
    - Al menos una letra mayúscula.
    - Al menos un símbolo (cualquier carácter que no sea letra o número).
    """
    # 1. Comprueba la longitud
    if not (8 <= len(password) <= 16):
        return False
        
    # 2. Comprueba que contenga al menos un número
    if not re.search(r'\d', password):
        return False
        
    # 3. Comprueba que contenga al menos una letra mayúscula
    if not re.search(r'[A-Z]', password):
        return False
        
    # 4. Comprueba que contenga al menos un símbolo
    if not re.search(r'[^a-zA-Z0-9]', password):
        return False
        
    # Si pasa todas las comprobaciones, la contraseña es válida
    return True