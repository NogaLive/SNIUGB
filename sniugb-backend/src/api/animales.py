from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from src.utils.security import get_current_user, get_db
from src.models.database_models import (
    Usuario, Animal, Predio,
    AnimalCondicionSalud,
    EventoSanitario, EventoSanitarioAnimal,
    EventoProduccion, ProduccionTipo,
    ControlCalidad, ControlCalidadAnimal,
    TipoEvento
)
from src.models.animal_models import (
    AnimalResponseSchema, AnimalDeleteConfirmationSchema, 
    AnimalDetailResponseSchema, AnimalUpdateSchema
)
from src.models.evento_models import (
    EventoSanitarioCreateSchema, EventoSanitarioResponseSchema,
    EventoProduccionCreateSchema, EventoProduccionResponseSchema,
    ControlCalidadCreateSchema, ControlCalidadResponseSchema,
)

animales_router = APIRouter(
    prefix="/animales",
    tags=["Animales (Individual / Eventos)"],
    route_class=APIRoute
)

# ---------------- EXISTENTES ----------------

@animales_router.get("/{cui}", response_model=AnimalDetailResponseSchema)
async def get_animal_detail(
    cui: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    animal = db.query(Animal).join(Animal.predio).filter(
        Animal.cui == cui,
        Predio.propietario_dni == current_user.numero_de_dni
    ).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal no encontrado.")
    return animal

@animales_router.put("/{cui}", response_model=AnimalResponseSchema)
async def update_animal_details(
    cui: str,
    animal_data: AnimalUpdateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    animal = db.query(Animal).join(Animal.predio).filter(
        Animal.cui == cui,
        Predio.propietario_dni == current_user.numero_de_dni
    ).first()
    if not animal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal no encontrado.")
    update_data = animal_data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(animal, k, v)
    try:
        db.commit()
        db.refresh(animal)
        return animal
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar el animal: {e}")

# ---------------- NUEVO: Helper tipos dinámicos ----------------

class TipoEventoResponse(BaseModel):
    id: int
    nombre: str
    grupo: str

@animales_router.get("/tipos/{grupo}", response_model=list[TipoEventoResponse])
async def listar_tipos_por_grupo(
    grupo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tipos = db.query(TipoEvento).filter(TipoEvento.grupo == grupo).order_by(TipoEvento.nombre.asc()).all()
    return [TipoEventoResponse(id=t.id, nombre=t.nombre, grupo=t.grupo) for t in tipos]

# ---------------- SANIDAD (MASIVO) ----------------

@animales_router.post("/eventos-sanitarios", status_code=status.HTTP_201_CREATED)
async def crear_evento_sanitario_masivo(
    payload: EventoSanitarioCreateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Validación tipos
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

    # Filtrar animales del usuario (mismo predio del usuario activo)
    animales = db.query(Animal).join(Animal.predio).filter(
        Animal.cui.in_(payload.animales_cui),
        Predio.propietario_dni == current_user.numero_de_dni
    ).all()
    if len(animales) == 0:
        raise HTTPException(status_code=404, detail="No se encontraron animales válidos del usuario.")

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
    db.flush()  # para obtener id

    # Asociaciones
    for a in animales:
        db.add(EventoSanitarioAnimal(evento_id=evento.id, animal_cui=a.cui))
        # Reglas de estado
        if payload.tipo_evento_tratamiento_id:
            a.condicion_salud = AnimalCondicionSalud.EN_OBSERVACION
        else:
            a.condicion_salud = AnimalCondicionSalud.ENFERMO

    db.commit()
    return {"id": evento.id, "cuids": [a.cui for a in animales], "detalle": "Evento sanitario registrado."}

# ---------------- PRODUCCIÓN (INDIVIDUAL) ----------------
# Mantengo la ruta por CUI que ya usabas

@animales_router.post("/{cui}/eventos-produccion", status_code=status.HTTP_201_CREATED)
async def create_evento_produccion(
    cui: str,
    evento_data: EventoProduccionCreateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    animal = db.query(Animal).join(Animal.predio).filter(
        Animal.cui == cui,
        Predio.propietario_dni == current_user.numero_de_dni
    ).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal no encontrado.")

    try:
        tipo = ProduccionTipo(evento_data.tipo_evento)
    except ValueError:
        raise HTTPException(status_code=422, detail="Tipo de producción inválido.")

    nuevo = EventoProduccion(
        animal_cui=cui,
        fecha_evento=evento_data.fecha_evento,
        tipo_evento=evento_data.tipo_evento,
        valor_cantidad=evento_data.valor_cantidad,
        unidad_medida=evento_data.unidad_medida,
        observaciones=evento_data.observaciones
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

# ---------------- CONTROL DE CALIDAD (MASIVO) ----------------

@animales_router.post("/control-calidad", status_code=status.HTTP_201_CREATED)
async def crear_control_calidad_masivo(
    payload: ControlCalidadCreateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # validar tipo CONTROL_CALIDAD
    tipo = db.query(TipoEvento).filter(
        TipoEvento.id == payload.tipo_evento_calidad_id,
        TipoEvento.grupo == "CONTROL_CALIDAD"
    ).first()
    if not tipo:
        raise HTTPException(status_code=422, detail="Tipo de control de calidad inválido.")

    # validar producto
    try:
        producto = ProduccionTipo(payload.producto)
        if producto == ProduccionTipo.PESAJE:
            raise ValueError()
    except Exception:
        raise HTTPException(status_code=422, detail="Producto inválido (LECHE/CARNE/CUERO).")

    # animales del usuario
    animales = db.query(Animal).join(Animal.predio).filter(
        Animal.cui.in_(payload.animales_cui),
        Predio.propietario_dni == current_user.numero_de_dni
    ).all()
    if len(animales) == 0:
        raise HTTPException(status_code=404, detail="No se encontraron animales válidos del usuario.")

    control = ControlCalidad(
        fecha_evento=payload.fecha_evento,
        tipo_evento_calidad_id=payload.tipo_evento_calidad_id,
        producto=producto,
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

# ---------------- DELETE/RESTORE (ya los tenías) ----------------

@animales_router.delete("/{cui}", status_code=status.HTTP_200_OK)
async def soft_delete_animal(
    cui: str,
    confirmation_data: AnimalDeleteConfirmationSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if cui != confirmation_data.confirmacion_cui:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El CUI de confirmación no coincide.")
    animal = db.query(Animal).join(Animal.predio).filter(
        Animal.cui == cui,
        Predio.propietario_dni == current_user.numero_de_dni
    ).first()
    if not animal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal no encontrado.")
    animal.estado = "en_papelera"
    db.commit()
    return {"message": f"El animal con CUI {cui} ha sido enviado a la papelera por 30 días."}

@animales_router.post("/{cui}/restaurar", status_code=status.HTTP_200_OK)
async def restore_animal(
    cui: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    animal = db.query(Animal).join(Animal.predio).filter(
        Animal.cui == cui,
        Animal.estado == "en_papelera",
        Predio.propietario_dni == current_user.numero_de_dni
    ).first()
    if not animal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal no encontrado en la papelera.")
    animal.estado = "activo"
    db.commit()
    return {"message": f"El animal con CUI {cui} ha sido restaurado."}
