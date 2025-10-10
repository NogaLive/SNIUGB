from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Literal

TipoEventoLiteral = Literal["Recordatorio", "Evento"]

class EventoResponseSchema(BaseModel):
    id: int
    fecha_evento: datetime
    titulo: str
    descripcion: str | None
    tipo: TipoEventoLiteral
    es_completado: bool
    estado_color: Literal["rojo", "verde", "amarillo", "gris"]
    origen_tipo: str | None = None
    es_editable: bool

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class RecordatorioCreateSchema(BaseModel):
    fecha_evento: date
    titulo: str
    descripcion: str | None = None

class RecordatorioUpdateSchema(BaseModel):
    fecha_evento: date | None = None
    titulo: str | None = None
    descripcion: str | None = None