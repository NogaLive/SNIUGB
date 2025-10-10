from pydantic import BaseModel, ConfigDict
from typing import Literal

class ContenidoAyudaResponseSchema(BaseModel):
    id: int
    tipo: Literal["FAQ", "Video"]
    pregunta_titulo: str
    respuesta_contenido: str | None
    video_url: str | None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class SolicitudSoporteCreateSchema(BaseModel):
    categoria: str
    mensaje: str