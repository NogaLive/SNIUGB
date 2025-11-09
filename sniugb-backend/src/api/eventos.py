from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from src.utils.security import get_current_user, get_db
from src.models.database_models import (
    Usuario, Animal, EventoSanitario, EventoProduccion, EventoHistorico
)
from src.models.schemas_eventos import (
    EventoSanitarioCreate, EventoProduccionCreate, EventoHistoricoCreate
)
from src.services.animales import aplicar_transicion_salud_por_evento

router = APIRouter(prefix="/eventos", tags=["Eventos"])

@router.post("/sanitarios", status_code=201)
def crear_evento_sanitario(payload: EventoSanitarioCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    # validar animales
    animales = db.query(Animal).filter(Animal.cui.in_(payload.animales_cui)).all()
    if not animales or len(animales) != len(set(payload.animales_cui)):
        raise HTTPException(400, "Algún CUI de animal no existe")
    ev = EventoSanitario(
        fecha_evento=payload.fecha_evento,
        tipos=",".join(payload.tipos),
        observaciones=payload.observaciones or "",
        tratamiento_tipo=payload.tratamiento_tipo,
        producto_nombre=payload.producto_nombre,
        dosis=payload.dosis,
        animales=animales
    )
    db.add(ev)
    aplicar_transicion_salud_por_evento(db, ev)
    db.commit()
    return {"id": ev.id}

@router.post("/produccion", status_code=201)
def crear_evento_produccion(payload: EventoProduccionCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if not db.query(Animal).filter_by(cui=payload.animal_cui).first():
        raise HTTPException(400, "Animal no existe")
    ev = EventoProduccion(**payload.model_dump())
    db.add(ev)
    db.commit()
    return {"id": ev.id}

@router.post("/historicos", status_code=201)
def crear_evento_historico(payload: EventoHistoricoCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if not db.query(Animal).filter_by(cui=payload.animal_cui).first():
        raise HTTPException(400, "Animal no existe")
    descendencia = ",".join(payload.descendencia_cuis) if payload.descendencia_cuis else None
    ev = EventoHistorico(
        animal_cui=payload.animal_cui,
        fecha_evento=payload.fecha_evento,
        tipo=payload.tipo,
        valor=payload.valor,
        unidad=payload.unidad,
        observaciones=payload.observaciones or "",
        descendencia_cuis=descendencia
    )
    db.add(ev)
    db.commit()
    return {"id": ev.id}