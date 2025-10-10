from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserCreateSchema(BaseModel):
    dni: str
    email: EmailStr
    telefono: str
    password: str

class UserResponseSchema(BaseModel):
    dni: str = Field(alias='numero_de_dni')
    nombre: str = Field(alias='nombre_completo')
    email: EmailStr
    estado: str
    fecha_de_registro: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

class UserUpdateProfileSchema(BaseModel):
    email: EmailStr | None = None
    telefono: str | None = None

class UserUpdatePasswordSchema(BaseModel):
    current_password: str
    new_password: str

class ForgotPasswordSchema(BaseModel):
    dni: str
    method: str

class ResetPasswordSchema(BaseModel):
    dni: str
    code: str
    new_password: str