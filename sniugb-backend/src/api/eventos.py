from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.utils.security import get_current_user, get_db
from src.models.database_models import (
    Usuario, Animal, Predio,
    AnimalCondicionSalud,
    EventoSanitario, EventoSanitarioAnimal,
    EventoProduccion, ProduccionTipo,
    ControlCalidad, ControlCalidadAnimal,
    TipoEvento
)
from src.models.evento_models import (
    EventoSanitarioCreateSchema,
    EventoProduccionCreateSchema,
    ControlCalidadCreateSchema,
)

router = APIRouter(prefix="/animales", tags=["Eventos"])

# ---------------- SANIDAD (MASIVO) ----------------
@router.post("/eventos-sanitarios", status_code=status.HTTP_201_CREATED)
def crear_evento_sanitario_masivo(
    payload: EventoSanitarioCreateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # validar tipos por grupo
    tipo_enf = db.query(TipoEvento).filter(
        TipoEvento.id == payload.tipo_evento_enfermedad_id,
        TipoEvento.grupo == "ENFERMEDAD"
    ).first()
    if not tipo_enf:
        raise HTTPException(status_code=422, detail="Tipo de ENFERMEDAD inválido.")

    tipo_trat = None
    if payload.tipo_evento_tratamiento_id:
        tipo_trat = db.query(TipoEvento).filter(
            TipoEvento.id == payload.tipo_evento_tratamiento_id,
            TipoEvento.grupo == "TRATAMIENTO"
        ).first()
        if not tipo_trat:
            raise HTTPException(status_code=422, detail="Tipo de TRATAMIENTO inválido.")

    # animales del usuario (por predio)
    animales = db.query(Animal).join(Animal.predio).filter(
        Animal.cui.in_(payload.animales_cui),
        Predio.propietario_dni == current_user.numero_de_dni
    ).all()
    if len(animales) == 0:
        raise HTTPException(status_code=404, detail="No se encontraron animales válidos del usuario.")

    # crear evento sanitario
    evento = EventoSanitario(
        fecha_evento_enfermedad=payload.fecha_evento_enfermedad,
        tipo_evento_enfermedad_id=payload.tipo_evento_enfermedad_id,
        fecha_evento_tratamiento=payload.fecha_evento_tratamiento,
        tipo_evento_tratamiento_id=payload.tipo_evento_tratamiento_id,
        nombre_tratamiento=payload.nombre_tratamiento,
        dosis=payload.dosis,
        unidad_medida_dosis=payload.unidad_medida_dosis,
        observaciones=payload.observaciones,
        creador_dni=current_user.numero_de_dni
    )
    db.add(evento)
    db.flush()

    # asociaciones + transición de salud
    for a in animales:
        db.add(EventoSanitarioAnimal(evento_id=evento.id, animal_cui=a.cui))
        if payload.tipo_evento_tratamiento_id:
            a.condicion_salud = AnimalCondicionSalud.EN_OBSERVACION
        else:
            a.condicion_salud = AnimalCondicionSalud.ENFERMO

    db.commit()
    return {"id": evento.id, "cuids": [a.cui for a in animales], "detalle": "Evento sanitario registrado."}

# ---------------- PRODUCCIÓN (INDIVIDUAL) ----------------
@router.post("/{cui}/eventos-produccion", status_code=status.HTTP_201_CREATED)
def crear_evento_produccion(
    cui: str,
    payload: EventoProduccionCreateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    animal = db.query(Animal).join(Animal.predio).filter(
        Animal.cui == cui,
        Predio.propietario_dni == current_user.numero_de_dni
    ).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal no encontrado.")

    # validación enum ProduccionTipo (Pydantic ya castea pero dejamos por claridad)
    try:
        _ = ProduccionTipo(payload.tipo_evento)
    except Exception:
        raise HTTPException(status_code=422, detail="Tipo de producción inválido.")

    ev = EventoProduccion(
        animal_cui=cui,
        fecha_evento=payload.fecha_evento,
        tipo_evento=payload.tipo_evento,
        valor_cantidad=payload.valor_cantidad,
        unidad_medida=payload.unidad_medida,
        observaciones=payload.observaciones
    )
    db.add(ev)
    db.commit()
    return {"id": ev.id}

# ---------------- CONTROL DE CALIDAD (MASIVO) ----------------
@router.post("/control-calidad", status_code=status.HTTP_201_CREATED)
def crear_control_calidad_masivo(
    payload: ControlCalidadCreateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # validar método de control (tipo_evento.grupo == CONTROL_CALIDAD)
    metodo = db.query(TipoEvento).filter(
        TipoEvento.id == payload.tipo_evento_calidad_id,
        TipoEvento.grupo == "CONTROL_CALIDAD"
    ).first()
    if not metodo:
        raise HTTPException(status_code=422, detail="Tipo de control de calidad inválido.")

    # producto (no PESAJE)
    if payload.producto.name == "PESAJE":
        raise HTTPException(status_code=422, detail="Producto inválido (LECHE/CARNE/CUERO).")

    animales = db.query(Animal).join(Animal.predio).filter(
        Animal.cui.in_(payload.animales_cui),
        Predio.propietario_dni == current_user.numero_de_dni
    ).all()
    if len(animales) == 0:
        raise HTTPException(status_code=404, detail="No se encontraron animales válidos del usuario.")

    control = ControlCalidad(
        fecha_evento=payload.fecha_evento,
        tipo_evento_calidad_id=payload.tipo_evento_calidad_id,
        producto=payload.producto,
        valor_cantidad=payload.valor_cantidad,
        unidad_medida=payload.unidad_medida,
        observaciones=payload.observaciones,
        creador_dni=current_user.numero_de_dni
    )
    db.add(control)
    db.flush()

    for a in animales:
        db.add(ControlCalidadAnimal(control_id=control.id, animal_cui=a.cui))

    db.commit()
    return {"id": control.id, "cuids": [a.cui for a in animales], "detalle": "Control de calidad registrado."}
