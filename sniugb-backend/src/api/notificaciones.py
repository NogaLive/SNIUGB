from fastapi import APIRouter, Depends, HTTPException
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from typing import List

from src.utils.security import get_current_user, get_db
from src.models.database_models import Usuario, Notificacion, Transferencia
from src.models.notificacion_models import NotificacionResponseSchema, NotificacionDetailResponseSchema

notificaciones_router = APIRouter(
    prefix="/notificaciones",
    tags=["Notificaciones"],
    route_class=APIRoute
)

@notificaciones_router.get("/", response_model=List[NotificacionResponseSchema])
async def get_mis_notificaciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene TODAS las notificaciones (leídas y no leídas) para el usuario actual,
    ordenadas por fecha de creación descendente.
    """
    notificaciones = db.query(Notificacion).filter(
        Notificacion.usuario_dni == current_user.numero_de_dni
    ).order_by(Notificacion.fecha_creacion.desc()).all()
    
    return notificaciones

@notificaciones_router.get("/contador-no-leidas")
async def get_contador_notificaciones_no_leidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Devuelve solo el NÚMERO de notificaciones no leídas para el usuario actual.
    Ideal para mostrar en un ícono de campana en el frontend.
    """
    count = db.query(Notificacion).filter(
        Notificacion.usuario_dni == current_user.numero_de_dni,
        Notificacion.leida == False
    ).count()
    
    return {"no_leidas": count}

@notificaciones_router.get("/{notificacion_id}", response_model=NotificacionDetailResponseSchema)
async def get_notificacion_detail(
    notificacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene el detalle completo de una notificación específica y la marca como leída.
    """
    notificacion = db.query(Notificacion).filter(
        Notificacion.id == notificacion_id,
        Notificacion.usuario_dni == current_user.numero_de_dni
    ).first()

    if notificacion is None:
        raise HTTPException(status_code=404, detail="Notificación no encontrada.")

    # Si la notificación no estaba leída, la marcamos como leída
    response_data = NotificacionDetailResponseSchema.model_validate(notificacion)
    
    # Si la notificación está relacionada con una transferencia, adjuntamos los detalles
    if notificacion.link and "/transferencias/" in notificacion.link:
        try:
            transferencia_id = int(notificacion.link.split("/")[-1])
            transferencia = db.query(Transferencia).filter(Transferencia.id == transferencia_id).first()
            if transferencia:
                response_data.detalles_transferencia = transferencia
        except (ValueError, IndexError):
            pass

    return response_data

@notificaciones_router.patch("/{notificacion_id}", response_model=NotificacionDetailResponseSchema)
async def marcar_notificacion_leida(
    notificacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    notificacion = db.query(Notificacion).filter(
        Notificacion.id == notificacion_id,
        Notificacion.usuario_dni == current_user.numero_de_dni
    ).first()
    if not notificacion:
        raise HTTPException(status_code=404, detail="Notificación no encontrada.")
    if not notificacion.leida:
        notificacion.leida = True
        db.commit()
        db.refresh(notificacion)
    return NotificacionDetailResponseSchema.model_validate(notificacion)
