from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from src.models.database_models import ProduccionTipoEnum, HistoricoTipoEnum

class EventoSanitarioCreate(BaseModel):
    fecha_evento: date
    tipos: List[str] = Field(min_items=1)
    observaciones: Optional[str] = ""
    animales_cui: List[str] = Field(min_items=1)
    # opcional (tratamiento)
    tratamiento_tipo: Optional[str] = None
    producto_nombre: Optional[str] = None
    dosis: Optional[str] = None

class EventoSanitarioOut(BaseModel):
    id: int
    fecha_evento: date
    tipos: List[str]
    observaciones: str
    animales_cui: List[str]
    class Config: from_attributes = True

class EventoProduccionCreate(BaseModel):
    animal_cui: str
    fecha_evento: date
    tipo: ProduccionTipoEnum
    valor: float
    unidad: str
    observaciones: Optional[str] = ""

class EventoHistoricoCreate(BaseModel):
    animal_cui: str
    fecha_evento: date
    tipo: HistoricoTipoEnum
    valor: Optional[float] = None
    unidad: Optional[str] = None
    observaciones: Optional[str] = ""
    descendencia_cuis: Optional[List[str]] = None
