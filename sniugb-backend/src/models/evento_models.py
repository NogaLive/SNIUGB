from pydantic import BaseModel
from datetime import datetime
from typing import Literal

# Usamos Literal para restringir los valores de tipo_evento
TipoSanitario = Literal["Vacunación", "Tratamiento", "Desparasitación"]
TipoProduccion = Literal["Pesaje", "Parto", "Control Lechero"]

# --- Esquemas para Eventos Sanitarios ---
class EventoSanitarioCreateSchema(BaseModel):
    fecha_evento: datetime
    tipo_evento: TipoSanitario
    producto_nombre: str
    dosis: str | None = None
    observaciones: str | None = None

class EventoSanitarioResponseSchema(BaseModel):
    id: int
    fecha_evento: datetime
    tipo_evento: str
    producto_nombre: str
    dosis: str | None
    observaciones: str | None

    class Config:
        from_attributes = True

# --- Esquemas para Eventos de Producción ---
class EventoProduccionCreateSchema(BaseModel):
    fecha_evento: datetime
    tipo_evento: TipoProduccion
    valor: str
    observaciones: str | None = None

class EventoProduccionResponseSchema(BaseModel):
    id: int
    fecha_evento: datetime
    tipo_evento: str
    valor: str
    observaciones: str | None

    class Config:
        from_attributes = True