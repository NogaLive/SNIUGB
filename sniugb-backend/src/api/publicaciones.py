from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import distinct

from src.utils.security import get_db
from src.models.database_models import Articulo
from src.models.articulo_models import ArticuloResponseSchema

publicaciones_router = APIRouter(prefix="/publicaciones", tags=["Publicaciones"])

@publicaciones_router.get("/", response_model=List[ArticuloResponseSchema])
async def get_publicaciones(skip: int = 0, limit: int = 10, categoria: str | None = None, db: Session = Depends(get_db)):
    """Obtiene una lista paginada de artículos, con filtro opcional por categoría."""
    query = db.query(Articulo).filter(Articulo.estado_publicacion == "publicado")
    if categoria:
        query = query.filter(Articulo.categoria == categoria)
    
    articulos = query.order_by(Articulo.fecha_publicacion.desc()).offset(skip).limit(limit).all()
    return articulos

@publicaciones_router.get("/categorias", response_model=List[str])
async def get_categorias_de_articulos(db: Session = Depends(get_db)):
    """
    Obtiene una lista de todas las categorías de artículos únicas que existen.
    """
    # Consulta a la base de datos para obtener valores únicos de la columna 'categoria'
    categorias_tuplas = db.query(distinct(Articulo.categoria)).all()
    # Convierte la lista de tuplas a una lista simple de strings
    categorias = [categoria[0] for categoria in categorias_tuplas]
    return categorias

@publicaciones_router.get("/{articulo_id}", response_model=ArticuloResponseSchema)
async def get_articulo_by_id(articulo_id: int, db: Session = Depends(get_db)):
    """Obtiene el detalle de un artículo específico."""
    articulo = db.query(Articulo).filter(Articulo.id == articulo_id, Articulo.estado_publicacion == "publicado").first()
    if not articulo:
        raise HTTPException(status_code=404, detail="Artículo no encontrado.")
    return articulo