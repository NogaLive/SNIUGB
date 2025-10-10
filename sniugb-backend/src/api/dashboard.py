from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case, Float
from datetime import datetime, timedelta
from src.utils.security import get_current_user, get_db
from src.models.database_models import Usuario, Predio, Animal, EventoProduccion, Transferencia, TransferenciaEstado, AnimalCondicionSalud
from src.models.dashboard_models import KPISchema

dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@dashboard_router.get("/{predio_codigo}/kpis", response_model=KPISchema)
async def get_dashboard_kpis(
    predio_codigo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Calcula y devuelve todos los KPIs principales para un predio específico."""
    predio = db.query(Predio).filter(Predio.codigo_predio == predio_codigo, Predio.propietario_dni == current_user.numero_de_dni).first()
    if not predio:
        raise HTTPException(status_code=404, detail="Predio no encontrado o no te pertenece.")

    # KPI 1: Total de Hato Activo
    total_hato = db.query(Animal).filter(Animal.predio_codigo == predio_codigo, Animal.estado == "activo").count()

    # KPI 2: Alertas de Salud
    alertas_salud = db.query(Animal).filter(
        Animal.predio_codigo == predio_codigo,
        Animal.condicion_salud.in_([AnimalCondicionSalud.ENFERMO, AnimalCondicionSalud.EN_OBSERVACION])
    ).count()

    # KPI 3: Tareas para hoy (suponiendo que tienes una tabla 'recordatorios' ligada al DNI)
    # Requerirá una tabla 'Recordatorio' que no hemos modelado aún. Por ahora, devolvemos 0.
    tareas_para_hoy = 0 

    # KPI 4: Producción Reciente (últimas 24h)
    hace_24_horas = datetime.utcnow() - timedelta(hours=24)

    # Suma de "kg" de eventos de pesaje
    prod_carne = db.query(func.sum(
        case((EventoProduccion.valor.like('%kg%'), func.cast(func.regexp_replace(EventoProduccion.valor, '[^0-9.]', '', 'g'), Float)), else_=0)
    )).join(Animal).filter(
        Animal.predio_codigo == predio_codigo,
        EventoProduccion.fecha_evento >= hace_24_horas,
        EventoProduccion.tipo_evento == 'Pesaje'
    ).scalar() or 0.0

    # Suma de "Lts" de eventos de control lechero
    prod_leche = db.query(func.sum(
        case((EventoProduccion.valor.like('%Lts%'), func.cast(func.regexp_replace(EventoProduccion.valor, '[^0-9.]', '', 'g'), Float)), else_=0)
    )).join(Animal).filter(
        Animal.predio_codigo == predio_codigo,
        EventoProduccion.fecha_evento >= hace_24_horas,
        EventoProduccion.tipo_evento == 'Control Lechero'
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
        "produccion_reciente_carne": prod_carne,
        "produccion_reciente_leche": prod_leche,
        "solicitudes_transferencia": solicitudes_transferencia
    }