from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List

from src.utils.security import get_db
from src.models import database_models as models
# CORRECCIÓN: Importamos los esquemas correctos desde admin_models
from src.models.admin_models import ArticulosResponse, ArticuloSchema 

publicaciones_router = APIRouter(
    prefix="/publicaciones",
    tags=["Publicaciones Públicas"],
)

@publicaciones_router.get("/", response_model=ArticulosResponse)
def get_publicaciones(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(6, ge=1),
    categoria_id: int | None = Query(None)
):
    """
    Obtiene una lista paginada de artículos para el público, con filtro opcional por ID de categoría.
    Devuelve un objeto con la lista de artículos y metadatos de paginación.
    """
    # 1. Construimos la consulta base con carga optimizada de relaciones (JOINs)
    query = db.query(models.Articulo).options(
        joinedload(models.Articulo.categoria),
        joinedload(models.Articulo.autor)
    ).filter(models.Articulo.estado_publicacion == "publicado")

    # 2. Aplicamos el filtro si se proporciona un ID de categoría
    if categoria_id is not None:
        query = query.filter(models.Articulo.categoria_id == categoria_id)
        
    # 3. Calculamos el total de artículos (después de filtrar)
    total_articulos = query.count()
    
    # 4. Aplicamos la paginación
    offset = (page - 1) * limit
    articulos = query.order_by(models.Articulo.fecha_publicacion.desc()).offset(offset).limit(limit).all()
    
    # 5. Calculamos el total de páginas
    total_pages = (total_articulos + limit - 1) // limit

    # 6. Devolvemos la respuesta en el formato que el frontend espera
    return {
        "articulos": articulos,
        "total": total_articulos,
        "page": page,
        "pages": total_pages
    }


@publicaciones_router.get("/{articulo_slug}", response_model=ArticuloSchema)
def get_articulo_by_slug(articulo_slug: str, db: Session = Depends(get_db)):
    """Obtiene el detalle de un artículo específico por su SLUG."""
    articulo = db.query(models.Articulo).options(
        joinedload(models.Articulo.categoria),
        joinedload(models.Articulo.autor)
    ).filter(
        models.Articulo.slug == articulo_slug, 
        models.Articulo.estado_publicacion == "publicado"
    ).first()
    
    if not articulo:
        raise HTTPException(status_code=404, detail="Artículo no encontrado.")
    
    # Incrementar el contador de vistas
    articulo.vistas += 1
    db.commit()
    db.refresh(articulo)
    
    return articulo