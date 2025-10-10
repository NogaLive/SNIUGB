from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.utils.security import get_current_user, get_db
from src.models.database_models import (
    Usuario, Animal, Predio, EventoSanitario, EventoProduccion, 
    EventoSanitarioTipo, EventoProduccionTipo, AnimalCondicionSalud
)
from src.models.animal_models import (
    AnimalResponseSchema, AnimalDeleteConfirmationSchema, 
    AnimalDetailResponseSchema, AnimalUpdateSchema
)
from src.models.evento_models import EventoSanitarioCreateSchema, EventoProduccionCreateSchema

animales_router = APIRouter(prefix="/animales", tags=["Animales (Individual)"])

@animales_router.get("/{cui}", response_model=AnimalDetailResponseSchema)
async def get_animal_detail(
    cui: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene el perfil detallado de un animal, incluyendo su historial."""
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
    """Actualiza los datos modificables de un animal específico."""
    animal = db.query(Animal).join(Animal.predio).filter(
        Animal.cui == cui,
        Predio.propietario_dni == current_user.numero_de_dni
    ).first()

    if not animal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal no encontrado.")

    update_data = animal_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(animal, key, value)
    
    try:
        db.commit()
        db.refresh(animal)
        return animal
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar el animal: {e}")

@animales_router.post("/{cui}/eventos-sanitarios", status_code=status.HTTP_201_CREATED)
async def create_evento_sanitario(
    cui: str,
    evento_data: EventoSanitarioCreateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Registra un nuevo evento de sanidad para un animal."""
    animal = db.query(Animal).join(Animal.predio).filter(
        Animal.cui == cui,
        Predio.propietario_dni == current_user.numero_de_dni
    ).first()

    if not animal:
        raise HTTPException(status_code=404, detail="Animal no encontrado.")

    # Actualizar la condición de salud del animal
    if evento_data.tipo_evento == "Tratamiento":
        animal.condicion_salud = AnimalCondicionSalud.ENFERMO
    
    evento_dict = evento_data.model_dump()
    tipo_evento_str = evento_dict.pop("tipo_evento")

    try:
        tipo_evento_enum = EventoSanitarioTipo(tipo_evento_str)
    except ValueError:
        raise HTTPException(
            status_code=422, 
            detail=f"'{tipo_evento_str}' no es un tipo de evento sanitario válido."
        )

    nuevo_evento = EventoSanitario(
        **evento_dict,
        animal_cui=cui,
        tipo_evento=tipo_evento_enum
    )
    
    db.add(nuevo_evento)
    db.commit()
    db.refresh(nuevo_evento)
    return nuevo_evento

@animales_router.post("/{cui}/eventos-produccion", status_code=status.HTTP_201_CREATED)
async def create_evento_produccion(
    cui: str,
    evento_data: EventoProduccionCreateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Registra un nuevo evento de producción para un animal."""
    animal = db.query(Animal).join(Animal.predio).filter(
        Animal.cui == cui,
        Predio.propietario_dni == current_user.numero_de_dni
    ).first()

    if not animal:
        raise HTTPException(status_code=404, detail="Animal no encontrado.")

    evento_dict = evento_data.model_dump()
    tipo_evento_str = evento_dict.pop("tipo_evento")

    try:
        tipo_evento_enum = EventoProduccionTipo(tipo_evento_str)
    except ValueError:
        raise HTTPException(
            status_code=422, 
            detail=f"'{tipo_evento_str}' no es un tipo de evento de producción válido."
        )

    nuevo_evento = EventoProduccion(
        **evento_dict,
        animal_cui=cui,
        tipo_evento=tipo_evento_enum
    )
    
    db.add(nuevo_evento)
    db.commit()
    db.refresh(nuevo_evento)
    return nuevo_evento

@animales_router.delete("/{cui}", status_code=status.HTTP_200_OK)
async def soft_delete_animal(
    cui: str,
    confirmation_data: AnimalDeleteConfirmationSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Envía un animal a la papelera (borrado lógico)."""
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
    """Restaura un animal desde la papelera."""
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