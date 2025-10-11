from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from src.utils.security import get_current_user, get_db
from src.models.database_models import Usuario, Predio, Animal, Raza, generate_predio_code
from src.models.predio_models import PredioCreateSchema, PredioResponseSchema
from src.models.animal_models import AnimalCreateSchema, AnimalResponseSchema
from src.services.animal_service import generar_nuevo_cui

predios_router = APIRouter(
    prefix="/predios",
    tags=["Predios"],
    route_class=APIRoute
)

@predios_router.post("/", response_model=PredioResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_predio(
    predio_data: PredioCreateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un nuevo predio para el usuario autenticado, asegurando un código único."""
    
    while True:
        codigo_unico = generate_predio_code()
        predio_existente = db.query(Predio).filter(Predio.codigo_predio == codigo_unico).first()
        if not predio_existente:
            break

    new_predio = Predio(
        codigo_predio=codigo_unico,
        nombre_predio=predio_data.nombre_predio,
        departamento=predio_data.departamento,
        ubicacion=predio_data.ubicacion,
        propietario_dni=current_user.numero_de_dni
    )
    db.add(new_predio)
    db.commit()
    db.refresh(new_predio)
    return new_predio

@predios_router.get("/me", response_model=List[PredioResponseSchema])
async def get_my_predios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene la lista de todos los predios del usuario autenticado."""
    return db.query(Predio).filter(Predio.propietario_dni == current_user.numero_de_dni).all()

@predios_router.delete("/{codigo_predio}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_predio(
    codigo_predio: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina un predio, solo si no tiene animales registrados."""
    predio = db.query(Predio).filter(Predio.codigo_predio == codigo_predio, Predio.propietario_dni == current_user.numero_de_dni).first()
    
    if not predio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Predio no encontrado.")
    
    animal_count = db.query(Animal).filter(Animal.predio_codigo == codigo_predio, Animal.estado == "activo").count()
    if animal_count > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"No se puede eliminar el predio porque tiene {animal_count} animales activos registrados.")
        
    db.delete(predio)
    db.commit()
    return None

@predios_router.get("/{codigo_predio}/animales", response_model=List[AnimalResponseSchema])
async def get_animales_by_predio(
    codigo_predio: str,
    estado: Optional[str] = Query("activo", enum=["activo", "en_papelera"]),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene la lista de animales de un predio específico,
    filtrando por estado ('activo' o 'en_papelera').
    """
    # 1. Verificar que el predio le pertenece al usuario
    predio = db.query(Predio).filter(
        Predio.codigo_predio == codigo_predio,
        Predio.propietario_dni == current_user.numero_de_dni
    ).first()

    if not predio:
        raise HTTPException(status_code=404, detail="Predio no encontrado o no te pertenece.")

    # 2. Consultar animales basado en el predio y el estado solicitado
    animales = db.query(Animal).filter(
        Animal.predio_codigo == codigo_predio,
        Animal.estado == estado
    ).all()

    return animales


@predios_router.post("/{codigo_predio}/animales", response_model=AnimalResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_animal_in_predio(
    codigo_predio: str,
    animal_data: AnimalCreateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un nuevo animal en un predio específico del usuario."""
    # 1. Verificar que el predio le pertenece al usuario
    predio = db.query(Predio).filter(
        Predio.codigo_predio == codigo_predio,
        Predio.propietario_dni == current_user.numero_de_dni
    ).first()

    if not predio:
        raise HTTPException(status_code=404, detail="El predio especificado no existe o no te pertenece.")
    
    raza_obj = db.query(Raza).filter(func.upper(Raza.nombre) == animal_data.raza.upper()).first()
    if not raza_obj:
        raise HTTPException(status_code=400, detail=f"La raza '{animal_data.raza}' no es válida.")

    try:
        nuevo_cui = generar_nuevo_cui(db=db, departamento_nombre=predio.departamento, raza_nombre=animal_data.raza)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    new_animal = Animal(
        cui=nuevo_cui,
        nombre=animal_data.nombre,
        raza=raza_obj,
        sexo=animal_data.sexo,
        fecha_nacimiento=animal_data.fecha_nacimiento,
        peso=animal_data.peso,
        predio_codigo=codigo_predio
    )
    
    try:
        db.add(new_animal)
        db.commit()
        db.refresh(new_animal)
        return new_animal
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al registrar el animal: {e}")