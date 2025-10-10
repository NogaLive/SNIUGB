from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List
from .transferencia_models import TransferenciaResponseSchema # Reutilizamos el esquema de transferencia

class NotificacionResponseSchema(BaseModel):
    id: int
    mensaje: str
    leida: bool
    fecha_creacion: datetime
    link: str | None

    class Config:
        from_attributes = True

class NotificacionDetailResponseSchema(NotificacionResponseSchema):
    # Añadimos un campo opcional que contendrá los detalles de la transferencia
    detalles_transferencia: TransferenciaResponseSchema | None = None