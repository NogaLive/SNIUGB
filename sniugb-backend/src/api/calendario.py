from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from sqlalchemy import extract, func, and_
from typing import List
from datetime import date, datetime, timezone, time

from src.utils.security import get_current_user, get_db
from src.models.database_models import (
    Usuario, Evento, CalendarioEventoTipo as TipoEvento, 
    Animal, InventarioItem, Predio
)
from src.models.calendario_models import (
    RecordatorioCreateSchema, EventoResponseSchema
)

calendario_router = APIRouter(
    prefix="/calendario",
    tags=["Calendario y Recordatorios"],
    route_class=APIRoute
)

def calcular_estado_color(evento: Evento, hoy: date) -> str:
    """Calcula el color del estado basado en las reglas de negocio."""
    fecha_evento_date = evento.fecha_evento.date()

    if evento.tipo == TipoEvento.EVENTO:
        return "amarillo"

    if evento.es_completado:
        return "verde"
    
    if fecha_evento_date < hoy:
        return "gris"

    return "rojo"

def format_evento_response(evento: Evento, hoy: date) -> dict:
    """Función helper para formatear la respuesta de un evento."""
    es_editable = (evento.tipo == TipoEvento.RECORDATORIO and evento.origen_tipo != "LOW_STOCK")
    estado_color = calcular_estado_color(evento, hoy)
    
    return {
        "id": evento.id,
        "fecha_evento": evento.fecha_evento,
        "titulo": evento.titulo,
        "descripcion": evento.descripcion,
        "tipo": evento.tipo.value,
        "es_completado": evento.es_completado,
        "estado_color": estado_color,
        "origen_tipo": evento.origen_tipo,
        "es_editable": es_editable
    }

@calendario_router.post("/recordatorios", response_model=EventoResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_recordatorio(
    recordatorio_data: RecordatorioCreateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un nuevo recordatorio manual para el usuario."""
    fecha_dt = datetime.combine(recordatorio_data.fecha_evento, time(0, 0), tzinfo=timezone.utc)
    
    nuevo_recordatorio = Evento(
        fecha_evento=fecha_dt,
        titulo=recordatorio_data.titulo,
        descripcion=recordatorio_data.descripcion,
        usuario_dni=current_user.numero_de_dni,
        tipo=TipoEvento.RECORDATORIO
    )
    db.add(nuevo_recordatorio)
    db.commit()
    db.refresh(nuevo_recordatorio)

    return format_evento_response(nuevo_recordatorio, date.today())

@calendario_router.get("/eventos/{year}/{month}", response_model=List[EventoResponseSchema])
async def get_eventos_del_mes(year: int, month: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """Obtiene todos los eventos y recordatorios de un mes, con su estado calculado."""
    hoy = date.today()
    response_list = []
    
    recordatorios_manuales = db.query(Evento).filter(
        Evento.usuario_dni == current_user.numero_de_dni,
        Evento.tipo == TipoEvento.RECORDATORIO,
        extract('year', Evento.fecha_evento) == year,
        extract('month', Evento.fecha_evento) == month
    ).all()
    for evento in recordatorios_manuales:
        response_list.append(format_evento_response(evento, hoy))

    animales_del_mes = db.query(Animal).join(Animal.predio).filter(
        Predio.propietario_dni == current_user.numero_de_dni,
        extract('month', Animal.fecha_nacimiento) == month
    ).all()
    
    for animal in animales_del_mes:
        cumple_fecha = animal.fecha_nacimiento.replace(year=year, tzinfo=timezone.utc)
        evento_temporal = Evento(id=0, fecha_evento=cumple_fecha, titulo=f"Aniv. Nacimiento: {animal.nombre}", tipo=TipoEvento.EVENTO, origen_tipo="ANIMAL_BIRTHDAY", es_completado=False)
        response_list.append(format_evento_response(evento_temporal, hoy))
        
    return response_list

@calendario_router.get("/recordatorios-activos", response_model=List[EventoResponseSchema])
async def get_recordatorios_activos(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """Obtiene los recordatorios para el 'Centro de Actividades'."""
    hoy = date.today()
    response_list = []
    
    recordatorios_manuales = db.query(Evento).filter(
        Evento.usuario_dni == current_user.numero_de_dni,
        Evento.tipo == TipoEvento.RECORDATORIO,
        Evento.es_completado == False,
        func.date(Evento.fecha_evento) >= hoy
    ).all()
    for recordatorio in recordatorios_manuales:
        response_list.append(format_evento_response(recordatorio, hoy))

    items_bajo_stock = db.query(InventarioItem).join(InventarioItem.predio).filter(
        Predio.propietario_dni == current_user.numero_de_dni,
        InventarioItem.cantidad_alerta != None,
        InventarioItem.stock <= InventarioItem.cantidad_alerta
    ).all()
    
    for item in items_bajo_stock:
        evento_temporal = Evento(
            id=0, fecha_evento=datetime.now(timezone.utc),
            titulo=f"Bajo stock: {item.nombre_item}",
            descripcion=f"Quedan {item.stock} {item.unidad_medida}. Umbral: {item.cantidad_alerta}.",
            tipo=TipoEvento.RECORDATORIO, origen_tipo="LOW_STOCK", es_completado=False
        )
        response_list.append(format_evento_response(evento_temporal, hoy))
        
    return response_list

@calendario_router.put("/recordatorios/{recordatorio_id}/toggle-complete", response_model=EventoResponseSchema)
async def toggle_complete_recordatorio(recordatorio_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """Marca un recordatorio como completado o no completado."""
    recordatorio = db.query(Evento).filter(Evento.id == recordatorio_id, Evento.usuario_dni == current_user.numero_de_dni).first()

    if not recordatorio or recordatorio.tipo != TipoEvento.RECORDATORIO:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado o no es editable.")

    if recordatorio.fecha_evento.date() < date.today() and recordatorio.es_completado:
        raise HTTPException(status_code=403, detail="No se puede cambiar el estado de un recordatorio pasado.")

    recordatorio.es_completado = not recordatorio.es_completado
    db.commit()
    db.refresh(recordatorio)
    
    return format_evento_response(recordatorio, date.today())

@calendario_router.delete("/recordatorios/{recordatorio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recordatorio(
    recordatorio_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina un recordatorio manual."""
    recordatorio = db.query(Evento).filter(
        Evento.id == recordatorio_id,
        Evento.usuario_dni == current_user.numero_de_dni,
        Evento.tipo == TipoEvento.RECORDATORIO
    ).first()

    if not recordatorio:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado o no es editable.")

    db.delete(recordatorio)
    db.commit()
    return None

from pydantic import BaseModel
class RecordatorioPatchState(BaseModel):
    es_completado: bool

@calendario_router.patch("/recordatorios/{recordatorio_id}", response_model=EventoResponseSchema)
async def patch_recordatorio_estado(
    recordatorio_id: int,
    body: RecordatorioPatchState,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    recordatorio = db.query(Evento).filter(
        Evento.id == recordatorio_id,
        Evento.usuario_dni == current_user.numero_de_dni,
        Evento.tipo == TipoEvento.RECORDATORIO
    ).first()

    if not recordatorio:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado o no es editable.")

    recordatorio.es_completado = bool(body.es_completado)
    db.commit()
    db.refresh(recordatorio)
    return format_evento_response(recordatorio, date.today())
