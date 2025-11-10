# src/api/dashboard.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, date, time

from src.utils.security import get_current_user, get_db
from src.models.database_models import (
    Usuario, Predio, Animal,
    EventoProduccion,
    Transferencia, TransferenciaEstado,
    AnimalCondicionSalud, Evento, CalendarioEventoTipo,
    ProduccionTipo
)
from src.models.dashboard_models import KPISchema

dashboard_router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    route_class=APIRoute
)

def rango_por_periodo(periodo: str):
    today = date.today()
    if periodo == "hoy":
        return (datetime.combine(today, time.min), datetime.combine(today, time.max))
    if periodo == "semana":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        return (datetime.combine(start, time.min), datetime.combine(end, time.max))
    # mes
    start = today.replace(day=1)
    next_start = (start + timedelta(days=32)).replace(day=1)
    end = next_start - timedelta(days=1)
    return (datetime.combine(start, time.min), datetime.combine(end, time.max))


@dashboard_router.get("/{predio_codigo}/kpis", response_model=KPISchema)
async def get_dashboard_kpis(
    predio_codigo: str,
    periodo: str = Query("hoy", enum=["hoy", "semana", "mes"]), 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificación de pertenencia del predio
    predio = db.query(Predio).filter(
        Predio.codigo_predio == predio_codigo,
        Predio.propietario_dni == current_user.numero_de_dni
    ).first()
    if not predio:
        raise HTTPException(status_code=404, detail="Predio no encontrado o no te pertenece.")

    start_dt, end_dt = rango_por_periodo(periodo)

    # KPI 1: Hato activo
    total_hato = db.query(Animal).filter(
        Animal.predio_codigo == predio_codigo,
        Animal.estado == "activo"
    ).count()

    # KPI 2: Alertas (estado != SANO)
    alertas_salud = db.query(Animal).filter(
        Animal.predio_codigo == predio_codigo,
        Animal.condicion_salud.in_([AnimalCondicionSalud.ENFERMO, AnimalCondicionSalud.EN_OBSERVACION])
    ).count()

    # KPI 3: Tareas (hoy)
    today = date.today()
    tareas_para_hoy = db.query(Evento).filter(
        Evento.usuario_dni == current_user.numero_de_dni,
        Evento.tipo == CalendarioEventoTipo.RECORDATORIO,
        Evento.es_completado == False,
        func.date(Evento.fecha_evento) == today
    ).count()

    # KPI 4: Producción por periodo (CARNE en kg, LECHE en litros)
    prod_carne = db.query(func.sum(EventoProduccion.valor_cantidad)).join(Animal).filter(
        Animal.predio_codigo == predio_codigo,
        EventoProduccion.fecha_evento.between(start_dt, end_dt),
        EventoProduccion.tipo_evento == ProduccionTipo.CARNE,
        EventoProduccion.unidad_medida.in_(["kg","Kg","KG"])
    ).scalar() or 0.0

    prod_leche = db.query(func.sum(EventoProduccion.valor_cantidad)).join(Animal).filter(
        Animal.predio_codigo == predio_codigo,
        EventoProduccion.fecha_evento.between(start_dt, end_dt),
        EventoProduccion.tipo_evento == ProduccionTipo.LECHE,
        EventoProduccion.unidad_medida.in_(["L","Lt","Lts","l"])
    ).scalar() or 0.0

    # KPI 5: Transferencias pendientes recibidas
    solicitudes_transferencia = db.query(Transferencia).filter(
        Transferencia.receptor_dni == current_user.numero_de_dni,
        Transferencia.estado == TransferenciaEstado.PENDIENTE
    ).count()

    return {
        "total_hato": total_hato,
        "alertas_salud": alertas_salud,
        "tareas_para_hoy": tareas_para_hoy,
        "produccion_reciente_carne": round(float(prod_carne), 2),
        "produccion_reciente_leche": round(float(prod_leche), 2),
        "solicitudes_transferencia": solicitudes_transferencia
    }

@dashboard_router.get("/{predio_codigo}/tabla")
async def get_tabla_dashboard(
    predio_codigo: str,
    tipo: str = Query(..., pattern="^(hato|alertas|tareas|produccion|transferencias)$"),
    periodo: str | None = Query(None, pattern="^(hoy|semana|mes)$"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    predio = db.query(Predio).filter(
        Predio.codigo_predio == predio_codigo,
        Predio.propietario_dni == current_user.numero_de_dni
    ).first()
    if not predio:
        raise HTTPException(status_code=404, detail="Predio no encontrado o no te pertenece.")

    def rango(periodo_str: str | None):
        if not periodo_str:
            return (datetime.min, datetime.max)
        return rango_por_periodo(periodo_str)

    start_dt, end_dt = rango(periodo)

    if tipo == "hato":
        animales = db.query(Animal).filter(
            Animal.predio_codigo == predio_codigo,
            Animal.estado == "activo"
        ).all()
        return [{
            "cui": a.cui,
            "nombre": a.nombre,
            "raza": getattr(a.raza, "nombre", None) if getattr(a, "raza", None) else None,
            "sexo": a.sexo,
            "fecha_nacimiento": a.fecha_nacimiento.isoformat() if a.fecha_nacimiento else None,
            "condicion_salud": a.condicion_salud.value if a.condicion_salud else None,
            "estado": a.estado
        } for a in animales]

    if tipo == "alertas":
        animales = db.query(Animal).filter(
            Animal.predio_codigo == predio_codigo,
            Animal.estado == "activo",
            Animal.condicion_salud.in_([AnimalCondicionSalud.ENFERMO, AnimalCondicionSalud.EN_OBSERVACION])
        ).all()
        return [{
            "cui": a.cui,
            "nombre": a.nombre,
            "raza": getattr(a.raza, "nombre", None) if getattr(a, "raza", None) else None,
            "sexo": a.sexo,
            "fecha_nacimiento": a.fecha_nacimiento.isoformat() if a.fecha_nacimiento else None,
            "condicion_salud": a.condicion_salud.value if a.condicion_salud else None,
            "estado": a.estado
        } for a in animales]

    if tipo == "tareas":
        eventos = db.query(Evento).filter(
            Evento.usuario_dni == current_user.numero_de_dni,
            Evento.tipo == CalendarioEventoTipo.RECORDATORIO,
            Evento.es_completado == False,
            Evento.fecha_evento.between(start_dt, end_dt)
        ).order_by(Evento.fecha_evento.desc()).all()
        return [{
            "fecha_evento": e.fecha_evento.isoformat() if e.fecha_evento else None,
            "titulo": e.titulo,
            "tipo": e.tipo.value if e.tipo else None
        } for e in eventos]

    if tipo == "produccion":
        eventos = db.query(EventoProduccion).join(Animal).filter(
            Animal.predio_codigo == predio_codigo,
            EventoProduccion.fecha_evento.between(start_dt, end_dt)
        ).order_by(EventoProduccion.fecha_evento.desc()).all()
        return [{
            "fecha_evento": ep.fecha_evento.isoformat() if ep.fecha_evento else None,
            "animal_cui": ep.animal_cui,
            "tipo_evento": ep.tipo_evento.value if ep.tipo_evento else None,
            "valor": f"{ep.valor_cantidad:g} {ep.unidad_medida}" if ep.unidad_medida else f"{ep.valor_cantidad:g}",
            "observaciones": ep.observaciones
        } for ep in eventos]

    if tipo == "transferencias":
        pendientes = db.query(Transferencia).filter(
            Transferencia.receptor_dni == current_user.numero_de_dni,
            Transferencia.estado == TransferenciaEstado.PENDIENTE
        ).order_by(Transferencia.fecha_solicitud.desc()).all()
        return [{
            "id": t.id,
            "solicitante": t.solicitante.nombre_completo if getattr(t, "solicitante", None) else t.solicitante_dni,
            "cantidad": len(t.animales) if getattr(t, "animales", None) is not None else None,
            "fecha_solicitud": t.fecha_solicitud.isoformat() if t.fecha_solicitud else None,
            "estado": t.estado.value if t.estado else None
        } for t in pendientes]
