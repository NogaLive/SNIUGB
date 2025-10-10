from pydantic import BaseModel

class PredioCreateSchema(BaseModel):
    nombre_predio: str
    departamento: str
    ubicacion: str

class PredioResponseSchema(BaseModel):
    codigo_predio: str
    nombre_predio: str
    departamento: str
    ubicacion: str

    class Config:
        from_attributes = True