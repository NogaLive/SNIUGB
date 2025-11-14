# src/services/animales.py
from __future__ import annotations
from typing import List
from sqlalchemy.orm import Session

from src.models.database_models import (
    Animal,
    AnimalCondicionSalud,
    EventoSanitario,
    EventoSanitarioAnimal,
)

def aplicar_transicion_salud_por_evento(db: Session, evento: EventoSanitario) -> None:
    """
    Regla de negocio solicitada:
      - Si se registra ENFERMEDAD (sin tratamiento): los animales pasan a ENFERMO.
      - Si el evento incluye TRATAMIENTO: los animales pasan a EN_OBSERVACION.
    El estado inicial fuera de eventos es SANO (no se toca aquí).
    """
    # 1) Obtener CUI de animales asociados
    cuis: List[str] = [
        x.animal_cui
        for x in db.query(EventoSanitarioAnimal.animal_cui).filter(
            EventoSanitarioAnimal.evento_id == evento.id
        ).all()
    ]

    # fallback por si el evento viene con relación cargada en memoria (no debería ser necesario)
    if not cuis and getattr(evento, "animales", None):
        cuis = [a.cui for a in (evento.animales or [])]

    if not cuis:
        return

    # 2) Determinar nuevo estado
    tiene_tratamiento = bool(getattr(evento, "tipo_evento_tratamiento_id", None))
    nuevo_estado = (
        AnimalCondicionSalud.EN_OBSERVACION if tiene_tratamiento else AnimalCondicionSalud.ENFERMO
    )

    # 3) Actualizar en bloque
    db.query(Animal).filter(Animal.cui.in_(cuis)).update(
        {Animal.condicion_salud: nuevo_estado},
        synchronize_session=False,
    )
