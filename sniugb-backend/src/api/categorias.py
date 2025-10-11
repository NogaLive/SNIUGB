from fastapi import APIRouter, Depends
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from typing import List
from src.utils.security import get_db
from src.models.database_models import Categoria
from src.models.admin_models import CategoriaSchema

categorias_router = APIRouter(
    prefix="/categorias",
    tags=["Categorías"],
    route_class=APIRoute
)

@categorias_router.get("/", response_model=List[CategoriaSchema])
async def get_all_categorias(db: Session = Depends(get_db)):
    """Obtiene la lista de todas las categorías con su nombre y URL de imagen."""
    return db.query(Categoria).all()