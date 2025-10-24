from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime

# CORRECCIÓN: Se añaden reglas de validación y se ajustan los nombres de campo
class UserCreateSchema(BaseModel):
    # Se usa el nombre de campo que espera la base de datos: 'numero_de_dni'
    numero_de_dni: str = Field(
        ..., 
        min_length=8, 
        max_length=8, 
        pattern=r'^[0-9]+$',
        description="El DNI debe tener 8 dígitos numéricos."
    )
    telefono: str = Field(
        ..., 
        min_length=9, 
        max_length=9, 
        pattern=r'^[0-9]+$',
        description="El teléfono debe tener 9 dígitos numéricos."
    )
    email: EmailStr # Pydantic valida automáticamente el formato del email
    password: str

class UserResponseSchema(BaseModel):
    numero_de_dni: str # Se elimina el alias, ya que el modelo de BD usa este nombre
    nombre_completo: str
    email: EmailStr
    estado: str
    fecha_de_registro: datetime

    model_config = ConfigDict(from_attributes=True)

class UserUpdateProfileSchema(BaseModel):
    email: EmailStr | None = None
    telefono: str | None = None

class UserUpdatePasswordSchema(BaseModel):
    current_password: str
    new_password: str

class ForgotPasswordSchema(BaseModel):
    numero_de_dni: str
    method: str

class VerifyCodeSchema(BaseModel):
    numero_de_dni: str
    code: str

class ResetPasswordSchema(BaseModel):
    numero_de_dni: str
    code: str
    new_password: str