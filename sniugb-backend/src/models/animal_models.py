from pydantic import BaseModel
from datetime import date
from typing import List
from .evento_models import EventoSanitarioResponseSchema, EventoProduccionResponseSchema

class AnimalCreateSchema(BaseModel):
    nombre: str
    raza: str
    sexo: str
    fecha_nacimiento: date
    peso: str

class RazaResponseSchema(BaseModel):
    nombre: str

    class Config:
        from_attributes = True

class AnimalResponseSchema(BaseModel):
    cui: str
    nombre: str
    raza: RazaResponseSchema
    sexo: str
    fecha_nacimiento: date
    peso: str
    predio_codigo: str
    estado: str

    class Config:
        from_attributes = True

class AnimalDeleteConfirmationSchema(BaseModel):
    confirmacion_cui: str

class AnimalDetailResponseSchema(AnimalResponseSchema):
    eventos_sanitarios: List[EventoSanitarioResponseSchema] = []
    eventos_produccion: List[EventoProduccionResponseSchema] = []

    class Config:
        from_attributes = True

class AnimalUpdateSchema(BaseModel):
    nombre: str | None = None
    sexo: str | None = None
    peso: str | None = None
    estado: str | None = None