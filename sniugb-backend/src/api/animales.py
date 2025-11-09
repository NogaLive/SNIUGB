from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from typing import List, Optional

from src.utils.security import get_current_user, get_db
from src.models.database_models import (
    Usuario, Animal, Predio,
    EventoSanitario, EventoProduccion, EventoHistorico,
    TipoEvento, TipoEventoGrupo, AnimalCondicionSalud,
    Catalogo
)
from src.models.animal_models import (
    AnimalResponseSchema, AnimalDeleteConfirmationSchema,
    AnimalDetailResponseSchema, AnimalUpdateSchema
)
# Puedes mantener tus Schemas existentes para crear eventos; aquí
# aceptamos dicts simples para encajar rápido con los cambios.
# Idealmente defines Pydantic Schemas nuevos (omito por brevedad).

animales_router = APIRouter(
    prefix="/animales",
    tags=["Animales (Individual)"],
    route_class=APIRoute
)

def ensure_owner(db: Session, cui: str, user: Usuario) -> Animal:
    animal = db.query(Animal).join(Animal.predio).filter(
        Animal.cui == cui,
        Predio.propietario_dni == user.numero_de_dni
    ).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal no encontrado.")
    return animal

@animales_router.get("/{cui}", response_model=AnimalDetailResponseSchema)
async def get_animal_detail(
    cui: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    animal = ensure_owner(db, cui, current_user)
    return animal

@animales_router.put("/{cui}", response_model=AnimalResponseSchema)
async def update_animal_details(
    cui: str,
    animal_data: AnimalUpdateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    animal = ensure_owner(db, cui, current_user)
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

# =========================
# SANITARIOS (multi-animal)
# =========================

@animales_router.post("/{cui}/eventos-sanitarios", status_code=status.HTTP_201_CREATED)
async def create_evento_sanitario(
    cui: str,
    payload: dict = Body(...)
    ,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea un evento sanitario. Acepta:
      {
        "fecha_evento": "YYYY-MM-DD",
        "tipo_evento": "Vacunación" | "Tratamiento" | "Desparasitación" | ... (definido en TipoEvento, grupo=SANITARIO),
        "producto_nombre": "...", "dosis":"...", "observaciones":"...",
        "tratamiento": "Antibiótico X" (opcional; Catalogo grupo='TRATAMIENTO'),
        "animales_cuis": ["...","..."] (opcional; si no viene, usa {cui})
      }
    Si el tipo tiene estado_resultante, se actualiza la condición de salud.
    """
    # valida animales
    animales_cuis: List[str] = payload.get("animales_cuis") or [cui]
    animales = []
    for acui in animales_cuis:
        animales.append(ensure_owner(db, acui, current_user))

    # tipo
    tipo_nombre = payload.get("tipo_evento")
    tipo = db.query(TipoEvento).filter(
        TipoEvento.grupo == TipoEventoGrupo.SANITARIO,
        TipoEvento.nombre == tipo_nombre
    ).first()
    if not tipo:
        raise HTTPException(status_code=422, detail=f"Tipo sanitario '{tipo_nombre}' no existe.")

    # tratamiento (opcional)
    trat_nombre = payload.get("tratamiento")
    trat = None
    if trat_nombre:
        trat = db.query(Catalogo).filter(
            Catalogo.grupo == "TRATAMIENTO", Catalogo.nombre == trat_nombre
        ).first()

    ev = EventoSanitario(
        fecha_evento=payload["fecha_evento"],
        tipo=tipo,
        tratamiento=trat,
        producto_nombre=payload.get("producto_nombre"),
        dosis=payload.get("dosis"),
        observaciones=payload.get("observaciones")
    )
    ev.animales = animales
    db.add(ev)

    # Transición de salud basada en tipo.estado_resultante (si está definido)
    if tipo.estado_resultante is not None:
        for a in animales:
            a.condicion_salud = tipo.estado_resultante

    db.commit()
    db.refresh(ev)
    return {"id": ev.id, "afectados": [a.cui for a in animales]}

# =========================
# PRODUCCIÓN (LECHE/CARNE/CUERO)
# =========================

@animales_router.post("/{cui}/eventos-produccion", status_code=status.HTTP_201_CREATED)
async def create_evento_produccion(
    cui: str,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Producción:
      {
        "fecha_evento": "YYYY-MM-DD",
        "tipo_evento": "LECHE" | "CARNE" | "CUERO",  (TipoEvento grupo=PRODUCCION)
        "valor": 12.34,
        "unidad": "Lt" | "Kg" | "Ud",
        "observaciones": "..."
      }
    """
    animal = ensure_owner(db, cui, current_user)

    tipo_nombre = payload.get("tipo_evento")
    tipo = db.query(TipoEvento).filter(
        TipoEvento.grupo == TipoEventoGrupo.PRODUCCION,
        TipoEvento.nombre == tipo_nombre
    ).first()
    if not tipo:
        raise HTTPException(status_code=422, detail=f"Tipo producción '{tipo_nombre}' no existe.")

    try:
        valor = float(payload["valor"])
    except Exception:
        raise HTTPException(status_code=422, detail="valor debe ser numérico")

    ev = EventoProduccion(
        animal_cui=animal.cui,
        fecha_evento=payload["fecha_evento"],
        tipo=tipo,
        valor=valor,
        unidad=payload.get("unidad") or ("Lt" if tipo.nombre == "LECHE" else "Kg"),
        observaciones=payload.get("observaciones")
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return {"id": ev.id}

# =========================
# HISTÓRICOS (Pesaje/Parto/Control Lechero)
# =========================

@animales_router.post("/{cui}/eventos-historicos", status_code=status.HTTP_201_CREATED)
async def create_evento_historico(
    cui: str,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Histórico:
      - Pesaje: { "fecha_evento", "tipo_evento":"Pesaje", "valor":float, "unidad":"Kg", "observaciones" }
      - Control Lechero (multi): { "fecha_evento", "tipo_evento":"Control Lechero", "animales_cuis":[...], "valor":?, "unidad":"?", ... } (valor/unidad opcional)
      - Parto: { "fecha_evento", "tipo_evento":"Parto", "descendencia_cuis":[...], "observaciones" }
              -> asigna madre/padre según sexo del progenitor {cui}
    """
    animal = ensure_owner(db, cui, current_user)

    tipo_nombre = payload.get("tipo_evento")
    tipo = db.query(TipoEvento).filter(
        TipoEvento.grupo == TipoEventoGrupo.HISTORICO,
        TipoEvento.nombre == tipo_nombre
    ).first()
    if not tipo:
        raise HTTPException(status_code=422, detail=f"Tipo histórico '{tipo_nombre}' no existe.")

    # multi-animal (p.ej. control lechero)
    animales: List[Animal] = [animal]
    if tipo.multi_animal:
        arr = payload.get("animales_cuis") or [cui]
        animales = [ensure_owner(db, acui, current_user) for acui in arr]

    valor = None
    if "valor" in payload and payload["valor"] is not None:
        try:
            valor = float(payload["valor"])
        except Exception:
            raise HTTPException(status_code=422, detail="valor debe ser numérico")

    ev = EventoHistorico(
        fecha_evento=payload["fecha_evento"],
        tipo=tipo,
        valor=valor,
        unidad=payload.get("unidad"),
        observaciones=payload.get("observaciones"),
    )
    ev.animales = animales

    # Si es PARTO, vincular descendencia y setear madre/padre en hijos
    if tipo.nombre.lower() == "parto":
        hijos: List[str] = payload.get("descendencia_cuis") or []
        if not hijos:
            raise HTTPException(status_code=422, detail="PARTO requiere descendencia_cuis")
        ev.descendencia_cuis = ",".join(hijos)

        # setea madre o padre en cada nuevo hijo según sexo del progenitor
        is_madre = (animal.sexo or "").lower().startswith("h")
        for child_cui in hijos:
            ch = db.query(Animal).filter(Animal.cui == child_cui).first()
            if not ch:
                # si aún no existe, lo dejamos para cuando se cree ese animal
                # (quedará solo en descendencia_cuis del evento)
                continue
            if is_madre:
                ch.madre_cui = animal.cui
            else:
                ch.padre_cui = animal.cui

    db.add(ev)
    db.commit()
    return {"id": ev.id, "animales": [a.cui for a in animales]}

# =========================
# BORRADO / RESTAURACIÓN
# =========================

@animales_router.delete("/{cui}", status_code=status.HTTP_200_OK)
async def soft_delete_animal(
    cui: str,
    confirmation_data: AnimalDeleteConfirmationSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if cui != confirmation_data.confirmacion_cui:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El CUI de confirmación no coincide.")
    animal = ensure_owner(db, cui, current_user)
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
