from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Literal
from .animal_models import AnimalResponseSchema
from src.models.database_models import TransferenciaEstado

class TransferenciaCreateSchema(BaseModel):
    animal_cuis: List[str]
    predio_destino_codigo: str

class TransferenciaApproveSchema(BaseModel):
    codigo_transferencia: str
    codigo_verificacion: str

class TransferenciaResponseSchema(BaseModel):
    id: int
    codigo_transferencia: str
    solicitante_dni: str
    receptor_dni: str
    predio_destino_codigo: str
    estado: TransferenciaEstado
    fecha_solicitud: datetime
    animales: List[AnimalResponseSchema]

    # 3. Actualiza la configuración para manejar Enums
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
    )