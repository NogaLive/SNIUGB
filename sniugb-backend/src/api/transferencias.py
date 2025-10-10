from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone, timedelta

from src.utils.security import get_current_user, get_db
from src.models.database_models import (
    Usuario, Animal, Predio, Transferencia, 
    TransferenciaEstado, Notificacion, TransferenciaAnimal
)
from src.models.transferencia_models import TransferenciaCreateSchema, TransferenciaResponseSchema, TransferenciaApproveSchema
from src.services.notification_service import send_transfer_request_email, send_transfer_request_whatsapp

transferencias_router = APIRouter(prefix="/transferencias", tags=["Transferencias"])

@transferencias_router.post("/solicitar", response_model=TransferenciaResponseSchema, status_code=status.HTTP_201_CREATED)
async def solicitar_transferencia(
    request: TransferenciaCreateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Inicia una solicitud de transferencia para una lista de animales, validando duplicados pendientes."""
    if not request.animal_cuis:
        raise HTTPException(status_code=400, detail="Debe seleccionar al menos un animal.")

    # Verificar que el predio de destino le pertenece al solicitante (comprador)
    predio_destino = db.query(Predio).filter(
        Predio.codigo_predio == request.predio_destino_codigo,
        Predio.propietario_dni == current_user.numero_de_dni
    ).first()
    if not predio_destino:
        raise HTTPException(status_code=404, detail="El predio de destino no es válido o no te pertenece.")

    animales_ya_solicitados = db.query(Animal.cui).join(
        TransferenciaAnimal, Animal.cui == TransferenciaAnimal.animal_cui
    ).join(
        Transferencia, TransferenciaAnimal.transferencia_id == Transferencia.id
    ).filter(
        Transferencia.estado == TransferenciaEstado.PENDIENTE,
        Animal.cui.in_(request.animal_cuis)
    ).all()

    if animales_ya_solicitados:
        cuis_bloqueados = [cui for cui, in animales_ya_solicitados]
        raise HTTPException(
            status_code=409,
            detail=f"No se puede crear la solicitud. Los siguientes animales ya están en una transferencia pendiente: {', '.join(cuis_bloqueados)}"
        )
    
    animales_a_transferir = db.query(Animal).filter(Animal.cui.in_(request.animal_cuis)).all()
    if len(animales_a_transferir) != len(set(request.animal_cuis)):
        raise HTTPException(status_code=404, detail="Uno o más CUIs de animales no fueron encontrados.")
    
    primer_animal = animales_a_transferir[0]
    receptor_dni = primer_animal.predio.propietario_dni
    if receptor_dni == current_user.numero_de_dni:
        raise HTTPException(status_code=400, detail="No puedes solicitar animales que ya te pertenecen.")
    
    for animal in animales_a_transferir:
        if animal.predio.propietario_dni != receptor_dni:
            raise HTTPException(status_code=400, detail="Todos los animales deben pertenecer al mismo propietario.")
        if animal.estado != "activo":
            raise HTTPException(status_code=400, detail=f"El animal {animal.cui} no está activo y no puede ser transferido.")

    try:
        # 1. Crear y guardar la solicitud de transferencia PRIMERO
        nueva_solicitud = Transferencia(
            solicitante_dni=current_user.numero_de_dni,
            receptor_dni=receptor_dni,
            predio_destino_codigo=request.predio_destino_codigo,
            animales=animales_a_transferir
        )
        db.add(nueva_solicitud)
        db.commit()
        db.refresh(nueva_solicitud) # Ahora 'nueva_solicitud.id' tiene un valor

        # 2. Crear la notificación AHORA que tenemos el ID
        nueva_notificacion = Notificacion(
            usuario_dni=receptor_dni,
            mensaje=f"Has recibido una solicitud de transferencia de {current_user.nombre_completo} para {len(nueva_solicitud.animales)} animal(es).",
            link=f"/transferencias/{nueva_solicitud.id}" # <-- Ahora esto funcionará
        )
        db.add(nueva_notificacion)
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear la solicitud: {e}")
    
    receptor = db.query(Usuario).filter(Usuario.numero_de_dni == receptor_dni).first()
    if receptor:
        send_transfer_request_email(
            to_email=receptor.email, 
            solicitante_nombre=current_user.nombre_completo,
            codigo=nueva_solicitud.codigo_confirmacion,
            animales=nueva_solicitud.animales
        )
        send_transfer_request_whatsapp(
            to_phone=receptor.telefono,
            solicitante_nombre=current_user.nombre_completo,
            codigo=nueva_solicitud.codigo_confirmacion,
            animales=nueva_solicitud.animales
        )

    return nueva_solicitud

@transferencias_router.post("/aprobar", response_model=TransferenciaResponseSchema)
async def aprobar_transferencia(
    request: TransferenciaApproveSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Aprueba una solicitud de transferencia usando el código de transferencia y el código de verificación."""
    solicitud = db.query(Transferencia).filter(
        Transferencia.codigo_transferencia == request.codigo_transferencia,
        Transferencia.receptor_dni == current_user.numero_de_dni
    ).first()

    if not solicitud:
        raise HTTPException(status_code=404, detail="Código de transferencia inválido o no te pertenece.")

    if solicitud.estado != TransferenciaEstado.PENDIENTE:
        raise HTTPException(status_code=400, detail=f"La solicitud ya no está pendiente (estado actual: {solicitud.estado.value}).")

    if solicitud.codigo_confirmacion != request.codigo_verificacion:
        raise HTTPException(status_code=403, detail="El código de verificación es incorrecto.")

    solicitud.estado = TransferenciaEstado.APROBADA
    for animal in solicitud.animales:
        animal.predio_codigo = solicitud.predio_destino_codigo
    
    db.commit()
    db.refresh(solicitud)
    return solicitud

@transferencias_router.get("/me", response_model=List[TransferenciaResponseSchema])
async def get_mis_transferencias(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """Obtiene las solicitudes de transferencia enviadas y recibidas por el usuario."""
    solicitudes = db.query(Transferencia).filter(
        (Transferencia.solicitante_dni == current_user.numero_de_dni) |
        (Transferencia.receptor_dni == current_user.numero_de_dni)
    ).order_by(Transferencia.fecha_solicitud.desc()).all()
    return solicitudes