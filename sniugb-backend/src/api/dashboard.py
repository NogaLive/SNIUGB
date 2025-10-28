from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from sqlalchemy import func, case, Float
from datetime import datetime, timedelta, date, time
from src.utils.security import get_current_user, get_db
from src.models.database_models import (
    Usuario, Predio, Animal, EventoProduccion, Transferencia, 
    TransferenciaEstado, AnimalCondicionSalud, Evento, CalendarioEventoTipo,
    EventoProduccionTipo  # <-- ASEGÚRATE DE IMPORTAR ESTO
)
from src.models.dashboard_models import KPISchema

dashboard_router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    route_class=APIRoute
)

@dashboard_router.get("/{predio_codigo}/kpis", response_model=KPISchema)
async def get_dashboard_kpis(
    predio_codigo: str,
    periodo: str = Query("hoy", enum=["hoy", "semana", "mes"]), 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Calcula y devuelve todos los KPIs principales para un predio específico."""
    predio = db.query(Predio).filter(Predio.codigo_predio == predio_codigo, Predio.propietario_dni == current_user.numero_de_dni).first()
    if not predio:
        raise HTTPException(status_code=404, detail="Predio no encontrado o no te pertenece.")

    # --- Lógica de Rango de Fechas ---
    today = date.today()
    start_date_dt = datetime.min
    end_date_dt = datetime.max

    if periodo == "hoy":
        start_date_dt = datetime.combine(today, time.min)
        end_date_dt = datetime.combine(today, time.max)
    elif periodo == "semana":
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        start_date_dt = datetime.combine(start_of_week, time.min)
        end_date_dt = datetime.combine(end_of_week, time.max)
    elif periodo == "mes":
        start_of_month = today.replace(day=1)
        next_month_start = (start_of_month + timedelta(days=32)).replace(day=1)
        end_of_month = next_month_start - timedelta(days=1)
        start_date_dt = datetime.combine(start_of_month, time.min)
        end_date_dt = datetime.combine(end_of_month, time.max)
    # -----------------------------------------------

    # KPI 1: Total de Hato Activo
    total_hato = db.query(Animal).filter(Animal.predio_codigo == predio_codigo, Animal.estado == "activo").count()

    # KPI 2: Alertas de Salud
    alertas_salud = db.query(Animal).filter(
        Animal.predio_codigo == predio_codigo,
        Animal.condicion_salud.in_([AnimalCondicionSalud.ENFERMO, AnimalCondicionSalud.EN_OBSERVACION])
    ).count()

    # KPI 3: Tareas para hoy
    tareas_para_hoy_query = db.query(Evento).filter(
        Evento.usuario_dni == current_user.numero_de_dni,
        Evento.tipo == CalendarioEventoTipo.RECORDATORIO,
        Evento.es_completado == False,
        func.date(Evento.fecha_evento) == today
    )
    tareas_para_hoy = tareas_para_hoy_query.count()

    # KPI 4: Producción Reciente (Carne)
    # ARREGLADO: Se usa el Enum 'EventoProduccionTipo.PESAJE' en lugar del string 'Pesaje'
    prod_carne = db.query(func.sum(
        case((EventoProduccion.valor.like('%kg%'), func.cast(func.regexp_replace(EventoProduccion.valor, '[^0-9.]', '', 'g'), Float)), else_=0)
    )).join(Animal).filter(
        Animal.predio_codigo == predio_codigo,
        EventoProduccion.fecha_evento.between(start_date_dt, end_date_dt),
        EventoProduccion.tipo_evento == EventoProduccionTipo.PESAJE # <-- ARREGLO
    ).scalar() or 0.0

    # KPI 4: Producción Reciente (Leche)
    # ARREGLADO: Se usa el Enum 'EventoProduccionTipo.CONTROL_LECHERO'
    prod_leche = db.query(func.sum(
        case((EventoProduccion.valor.like('%Lts%'), func.cast(func.regexp_replace(EventoProduccion.valor, '[^0-9.]', '', 'g'), Float)), else_=0)
    )).join(Animal).filter(
        Animal.predio_codigo == predio_codigo,
        EventoProduccion.fecha_evento.between(start_date_dt, end_date_dt),
        EventoProduccion.tipo_evento == EventoProduccionTipo.CONTROL_LECHERO # <-- ARREGLO
    ).scalar() or 0.0

    # KPI 5: Solicitudes de Transferencia Recibidas
    solicitudes_transferencia = db.query(Transferencia).filter(
        Transferencia.receptor_dni == current_user.numero_de_dni,
        Transferencia.estado == TransferenciaEstado.PENDIENTE
    ).count()

    return {
        "total_hato": total_hato,
        "alertas_salud": alertas_salud,
        "tareas_para_hoy": tareas_para_hoy,
        "produccion_reciente_carne": round(prod_carne, 2),
        "produccion_reciente_leche": round(prod_leche, 2),
        "solicitudes_transferencia": solicitudes_transferencia
    }