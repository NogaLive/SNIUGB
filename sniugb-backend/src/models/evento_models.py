# src/models/evento_models.py
from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime

# Usamos los enums reales del modelo de BD
from src.models.database_models import ProduccionTipo

# ============================================================
# SANIDAD (evento principal + asociación masiva a animales)
# ============================================================

class EventoSanitarioCreateSchema(BaseModel):
    # Obligatorio (flujo normal): ENFERMEDAD
    fecha_evento_enfermedad: datetime
    tipo_evento_enfermedad_id: int  # de tipo_evento.grupo == "ENFERMEDAD"

    # Opcional (puede llenarse después): TRATAMIENTO
    fecha_evento_tratamiento: Optional[datetime] = None
    tipo_evento_tratamiento_id: Optional[int] = None  # de tipo_evento.grupo == "TRATAMIENTO"
    nombre_tratamiento: Optional[str] = None
    dosis: Optional[float] = None
    unidad_medida_dosis: Optional[str] = None

    observaciones: Optional[str] = None

    # Selección masiva: se guarda en evento_sanitario_animales
    animales_cui: List[str] = Field(default_factory=list, description="Lista de CUI de animales del predio")

class EventoSanitarioResponseSchema(BaseModel):
    id: int
    fecha_evento_enfermedad: datetime
    tipo_evento_enfermedad_id: int
    fecha_evento_tratamiento: Optional[datetime] = None
    tipo_evento_tratamiento_id: Optional[int] = None
    nombre_tratamiento: Optional[str] = None
    dosis: Optional[float] = None
    unidad_medida_dosis: Optional[str] = None
    observaciones: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================
# PRODUCCIÓN (una producción por animal; incluye PESAJE)
# ============================================================

class EventoProduccionCreateSchema(BaseModel):
    # Nota: aquí el CUI es individual (no masivo)
    animal_cui: str
    fecha_evento: datetime
    tipo_evento: ProduccionTipo  # LECHE/CARNE/CUERO/PESAJE
    valor_cantidad: Optional[float] = None
    unidad_medida: Optional[str] = None  # kg, g, L, ml, etc.
    observaciones: Optional[str] = None

class EventoProduccionResponseSchema(BaseModel):
    id: int
    animal_cui: str
    fecha_evento: datetime
    tipo_evento: ProduccionTipo
    valor_cantidad: Optional[float] = None
    unidad_medida: Optional[str] = None
    observaciones: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================
# CONTROL DE CALIDAD (evento + asociación masiva a animales)
# ============================================================

class ControlCalidadCreateSchema(BaseModel):
    fecha_evento: datetime
    # Debe existir en tipo_evento con grupo == "CONTROL_CALIDAD"
    tipo_evento_calidad_id: int

    # Producto a evaluar (solo LECHE/CARNE/CUERO; PESAJE no aplica aquí)
    producto: ProduccionTipo
    valor_cantidad: Optional[float] = None
    unidad_medida: Optional[str] = None
    observaciones: Optional[str] = None

    # Asociación masiva
    animales_cui: List[str] = Field(default_factory=list)

    @validator("producto")
    def validar_producto_sin_pesaje(cls, v: ProduccionTipo) -> ProduccionTipo:
        if v == ProduccionTipo.PESAJE:
            raise ValueError("El producto para Control de Calidad debe ser LECHE, CARNE o CUERO (no PESAJE).")
        return v

class ControlCalidadResponseSchema(BaseModel):
    id: int
    fecha_evento: datetime
    tipo_evento_calidad_id: int
    producto: ProduccionTipo
    valor_cantidad: Optional[float] = None
    unidad_medida: Optional[str] = None
    observaciones: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================
# HISTÓRICOS (opcional: partos, muerte, compra, etc.)
# ============================================================

class EventoHistoricoCreateSchema(BaseModel):
    animal_cui: str
    fecha_evento: datetime
    tipo: str  # de acuerdo a tu modelo en BD
    valor: Optional[float] = None
    unidad: Optional[str] = None
    observaciones: Optional[str] = None
    descendencia_cuis: Optional[List[str]] = None  # se guardará como CSV

class EventoHistoricoResponseSchema(BaseModel):
    id: int
    animal_cui: str
    fecha_evento: datetime
    tipo: str
    valor: Optional[float] = None
    unidad: Optional[str] = None
    observaciones: Optional[str] = None
    descendencia_cuis: Optional[str] = None

    class Config:
        from_attributes = True