from pydantic import BaseModel
from datetime import datetime
from .transferencia_models import TransferenciaResponseSchema # Reutilizamos el esquema de transferencia

class NotificacionResponse(BaseModel):
    id: int
    mensaje: str
    leida: bool
    fecha_creacion: datetime
    link: str | None = None

    class Config:
        from_attributes = True

class NotificacionDetailResponse(NotificacionResponse):
    # Añadimos un campo opcional que contendrá los detalles de la transferencia
    detalles_transferencia: TransferenciaResponseSchema | None = None