from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, or_
from sqlalchemy.dialects.postgresql import ENUM
from pydantic import BaseModel, field_validator
from typing import Optional, List

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

# ============================================================
# Router
# ============================================================
animales_router = APIRouter(
    prefix="/animales",
    tags=["Animales (Individual / Eventos)"],
    route_class=APIRoute
)

# ==========================
# ENUM PG para el "grupo"
# ==========================
PG_TIPO_EVENTO_GRUPO = ENUM(
    'ENFERMEDAD', 'TRATAMIENTO', 'CONTROL_CALIDAD',
    name='tipo_evento_grupo_enum',
    create_type=False
)

# ------------------------------------------------------------
# Helpers / DTOs que ALINEAN con tu Front (user.ts/html)
# ------------------------------------------------------------

class TipoEventoResponse(BaseModel):
    id: int
    nombre: str
    grupo: str

def _enum_val(x):
    return x.value if hasattr(x, "value") else x

# ---- Sanitarios (masivo) acorde al front ----
class EventoSanitarioMasivoIn(BaseModel):
    fecha_evento_enfermedad: str
    tipo_evento_enfermedad_id: int
    fecha_evento_tratamiento: Optional[str] = None
    tipo_evento_tratamiento_id: Optional[int] = None
    nombre_tratamiento: Optional[str] = None
    dosis: Optional[float] = None
    unidad_medida_dosis: Optional[str] = None
    observaciones: Optional[str] = None
    animales_cui: List[str]

# ---- Producción (individual): front envía "producto" y "valor" ----
class EventoProduccionIn(BaseModel):
    fecha_evento: str
    producto: str  # LECHE | CARNE | CUERO (front)
    valor: Optional[float] = None  # front usa "valor"
    unidad_medida: Optional[str] = None
    observaciones: Optional[str] = None

    @field_validator('producto')
    @classmethod
    def validar_producto(cls, v: str) -> str:
        v = (v or '').upper()
        if v not in ('LECHE', 'CARNE', 'CUERO'):
            raise ValueError('Producto inválido (LECHE/CARNE/CUERO)')
        return v

# ---- Control de calidad (masivo): tolera "metodo_id" del front ----
class ControlCalidadMasivoIn(BaseModel):
    fecha_evento: str
    producto: str  # LECHE | CARNE | CUERO
    valor_cantidad: Optional[float] = None
    unidad_medida: Optional[str] = None
    observaciones: Optional[str] = None
    animales_cui: List[str]
    tipo_evento_calidad_id: Optional[int] = None
    metodo_id: Optional[int] = None  # alias que manda el front

    @field_validator('producto')
    @classmethod
    def validar_producto(cls, v: str) -> str:
        v = (v or '').upper()
        if v not in ('LECHE', 'CARNE', 'CUERO'):
            raise ValueError('Producto inválido (LECHE/CARNE/CUERO)')
        return v

    def resolved_tipo_evento_id(self) -> int:
        v = self.tipo_evento_calidad_id or self.metodo_id
        if not v:
            raise ValueError('Se requiere tipo_evento_calidad_id (o metodo_id).')
        return int(v)

# ---- Crear Animal acorde al front ----
class AnimalCreateSchema(BaseModel):
    cui: str
    nombre: Optional[str] = None
    sexo: str  # 'MACHO' | 'HEMBRA'
    raza: str
    fecha_nacimiento: str  # YYYY-MM-DD
    predio_codigo: str

# ============================================================
# EXISTENTES: detalle/actualización
# ============================================================

@animales_router.get("/{cui}", response_model=AnimalDetailResponseSchema)
async def get_animal_detail(
    cui: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    animal = (
        db.query(Animal)
        .join(Animal.predio)
        .filter(
            Animal.cui == cui,
            Predio.propietario_dni == current_user.numero_de_dni
        )
        .first()
    )
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
    animal = (
        db.query(Animal)
        .join(Animal.predio)
        .filter(
            Animal.cui == cui,
            Predio.propietario_dni == current_user.numero_de_dni
        )
        .first()
    )
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

# ============================================================
# NUEVOS: soporte a la UI (chips/sugerencias y alta de animal)
# ============================================================

@animales_router.get("", response_model=list[AnimalResponseSchema])
async def list_animales(
    predio: str = Query(..., description="Código de predio (del usuario actual)"),
    q: str = Query("", description="Búsqueda por CUI o nombre"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # Verifica que el predio pertenezca al usuario actual
    predio_obj = (
        db.query(Predio)
        .filter(
            Predio.codigo_predio == predio,
            Predio.propietario_dni == current_user.numero_de_dni
        )
        .first()
    )
    if not predio_obj:
        raise HTTPException(status_code=404, detail="Predio no encontrado o no autorizado.")

    qs = (
        db.query(Animal)
        .join(Animal.predio)
        .filter(
            Predio.codigo_predio == predio,
            Predio.propietario_dni == current_user.numero_de_dni
        )
    )
    if q:
        like = f"%{q.strip()}%"
        qs = qs.filter(or_(Animal.cui.ilike(like), Animal.nombre.ilike(like)))

    results = qs.order_by(Animal.cui.asc()).limit(50).all()
    return results

@animales_router.post("", response_model=AnimalResponseSchema, status_code=status.HTTP_201_CREATED)
async def crear_animal(
    payload: AnimalCreateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # Validar predio del usuario
    predio = (
        db.query(Predio)
        .filter(
            Predio.codigo_predio == payload.predio_codigo,
            Predio.propietario_dni == current_user.numero_de_dni
        )
        .first()
    )
    if not predio:
        raise HTTPException(status_code=404, detail="Predio no encontrado o no autorizado.")

    # Evitar duplicados de CUI
    exists = db.query(Animal).filter(Animal.cui == payload.cui).first()
    if exists:
        raise HTTPException(status_code=409, detail="Ya existe un animal con ese CUI.")

    animal = Animal(
        cui=payload.cui,
        nombre=payload.nombre,
        sexo=payload.sexo,
        raza=payload.raza,  # si es FK en tu modelo, adapta el mapeo aquí
        fecha_nacimiento=payload.fecha_nacimiento,
        predio_id=predio.id
    )
    db.add(animal)
    db.commit()
    db.refresh(animal)
    return animal

# ============================================================
# Tipos de evento dinámicos
# ============================================================

@animales_router.get("/tipos/{grupo}", response_model=list[TipoEventoResponse])
async def listar_tipos_por_grupo(
    grupo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tipos = (
        db.query(TipoEvento)
          .filter(TipoEvento.grupo == cast(grupo, PG_TIPO_EVENTO_GRUPO))
          .order_by(TipoEvento.nombre.asc())
          .all()
    )
    return [TipoEventoResponse(id=t.id, nombre=t.nombre, grupo=_enum_val(t.grupo)) for t in tipos]

# ============================================================
# SANIDAD (MASIVO)
# ============================================================

@animales_router.post("/eventos-sanitarios", status_code=status.HTTP_201_CREATED)
async def crear_evento_sanitario_masivo(
    payload: EventoSanitarioMasivoIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Validar tipos
    tipo_enf = db.query(TipoEvento).filter(
        TipoEvento.id == payload.tipo_evento_enfermedad_id,
        TipoEvento.grupo == cast('ENFERMEDAD', PG_TIPO_EVENTO_GRUPO)
    ).first()
    if not tipo_enf:
        raise HTTPException(status_code=422, detail="Tipo de ENFERMEDAD inválido.")

    tipo_trat = None
    if payload.tipo_evento_tratamiento_id:
        tipo_trat = db.query(TipoEvento).filter(
            TipoEvento.id == payload.tipo_evento_tratamiento_id,
            TipoEvento.grupo == cast('TRATAMIENTO', PG_TIPO_EVENTO_GRUPO)
        ).first()
        if not tipo_trat:
            raise HTTPException(status_code=422, detail="Tipo de TRATAMIENTO inválido.")

    # Filtrar animales del usuario (por dueño del predio)
    animales = (
        db.query(Animal)
        .join(Animal.predio)
        .filter(
            Animal.cui.in_(payload.animales_cui),
            Predio.propietario_dni == current_user.numero_de_dni
        )
        .all()
    )
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
    db.flush()  # id

    # Asociaciones + reglas de estado
    for a in animales:
        db.add(EventoSanitarioAnimal(evento_id=evento.id, animal_cui=a.cui))
        if payload.tipo_evento_tratamiento_id:
            a.condicion_salud = AnimalCondicionSalud.EN_OBSERVACION
        else:
            a.condicion_salud = AnimalCondicionSalud.ENFERMO

    db.commit()
    return {"id": evento.id, "cuids": [a.cui for a in animales], "detalle": "Evento sanitario registrado."}

# ============================================================
# PRODUCCIÓN (INDIVIDUAL)
# ============================================================

@animales_router.post("/{cui}/eventos-produccion", status_code=status.HTTP_201_CREATED)
async def create_evento_produccion(
    cui: str,
    evento_data: EventoProduccionIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    animal = (
        db.query(Animal)
        .join(Animal.predio)
        .filter(
            Animal.cui == cui,
            Predio.propietario_dni == current_user.numero_de_dni
        )
        .first()
    )
    if not animal:
        raise HTTPException(status_code=404, detail="Animal no encontrado.")

    try:
        tipo = ProduccionTipo(evento_data.producto)  # LECHE/CARNE/CUERO
    except ValueError:
        raise HTTPException(status_code=422, detail="Producto inválido.")

    nuevo = EventoProduccion(
        animal_cui=cui,
        fecha_evento=evento_data.fecha_evento,
        tipo_evento=tipo,  # enum
        valor_cantidad=evento_data.valor,
        unidad_medida=evento_data.unidad_medida,
        observaciones=evento_data.observaciones
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

# ============================================================
# CONTROL DE CALIDAD (MASIVO)
# ============================================================

@animales_router.post("/control-calidad", status_code=status.HTTP_201_CREATED)
async def crear_control_calidad_masivo(
    payload: ControlCalidadMasivoIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        producto = ProduccionTipo(payload.producto)
        if producto.name.upper() == 'PESAJE':
            raise ValueError()
    except Exception:
        raise HTTPException(status_code=422, detail="Producto inválido (LECHE/CARNE/CUERO).")

    tipo_id = payload.resolved_tipo_evento_id()
    tipo = db.query(TipoEvento).filter(
        TipoEvento.id == tipo_id,
        TipoEvento.grupo == cast('CONTROL_CALIDAD', PG_TIPO_EVENTO_GRUPO)
    ).first()
    if not tipo:
        raise HTTPException(status_code=422, detail="Tipo de control de calidad inválido.")

    animales = (
        db.query(Animal)
        .join(Animal.predio)
        .filter(
            Animal.cui.in_(payload.animales_cui),
            Predio.propietario_dni == current_user.numero_de_dni
        )
        .all()
    )
    if len(animales) == 0:
        raise HTTPException(status_code=404, detail="No se encontraron animales válidos del usuario.")

    control = ControlCalidad(
        fecha_evento=payload.fecha_evento,
        tipo_evento_calidad_id=tipo.id,
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

# ============================================================
# DELETE / RESTORE
# ============================================================

@animales_router.delete("/{cui}", status_code=status.HTTP_200_OK)
async def soft_delete_animal(
    cui: str,
    confirmation_data: AnimalDeleteConfirmationSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if cui != confirmation_data.confirmacion_cui:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El CUI de confirmación no coincide.")
    animal = (
        db.query(Animal)
        .join(Animal.predio)
        .filter(
            Animal.cui == cui,
            Predio.propietario_dni == current_user.numero_de_dni
        )
        .first()
    )
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
    animal = (
        db.query(Animal)
        .join(Animal.predio)
        .filter(
            Animal.cui == cui,
            Animal.estado == "en_papelera",
            Predio.propietario_dni == current_user.numero_de_dni
        )
        .first()
    )
    if not animal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal no encontrado en la papelera.")
    animal.estado = "activo"
    db.commit()
    return {"message": f"El animal con CUI {cui} ha sido restaurado."}