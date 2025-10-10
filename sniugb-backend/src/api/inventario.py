from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.utils.security import get_current_user, get_db
from src.models.database_models import Usuario, Predio, InventarioItem, InventarioCategoria
from src.models.inventario_models import InventarioItemCreateSchema, InventarioItemResponseSchema, InventarioItemUpdateSchema

inventario_router = APIRouter(prefix="/inventario", tags=["Inventario"])

@inventario_router.post("/{predio_codigo}", response_model=InventarioItemResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_inventario_item(
    predio_codigo: str,
    item_data: InventarioItemCreateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un nuevo item en el inventario de un predio específico."""
    predio = db.query(Predio).filter(Predio.codigo_predio == predio_codigo, Predio.propietario_dni == current_user.numero_de_dni).first()
    if not predio:
        raise HTTPException(status_code=404, detail="Predio no encontrado o no te pertenece.")

    nuevo_item = InventarioItem(
        **item_data.model_dump(),
        predio_codigo=predio_codigo
    )
    
    db.add(nuevo_item)
    db.commit()
    db.refresh(nuevo_item)
    return nuevo_item

@inventario_router.get("/{predio_codigo}", response_model=List[InventarioItemResponseSchema])
async def get_inventario_by_predio(
    predio_codigo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene todos los items del inventario de un predio."""
    predio = db.query(Predio).filter(Predio.codigo_predio == predio_codigo, Predio.propietario_dni == current_user.numero_de_dni).first()
    if not predio:
        raise HTTPException(status_code=404, detail="Predio no encontrado o no te pertenece.")
    
    return db.query(InventarioItem).filter(InventarioItem.predio_codigo == predio_codigo).all()

@inventario_router.put("/{item_id}", response_model=InventarioItemResponseSchema)
async def update_inventario_item(
    item_id: int,
    item_data: InventarioItemUpdateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza un item del inventario."""
    item = db.query(InventarioItem).join(InventarioItem.predio).filter(
        InventarioItem.id == item_id,
        Predio.propietario_dni == current_user.numero_de_dni
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item de inventario no encontrado.")
        
    update_data = item_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    
    db.commit()
    db.refresh(item)
    return item