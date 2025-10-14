from slugify import slugify
from sqlalchemy.orm import Session
from ..models import database_models as models

def generate_unique_slug(db: Session, title: str) -> str:
    """
    Genera un slug único para un artículo. Si el slug base ya existe,
    le anexa un número incremental (-2, -3, etc.) hasta encontrar uno único.
    """
    base_slug = slugify(title)
    slug = base_slug
    counter = 1

    while True:
        # Busca si ya existe un artículo con el slug generado
        existing_article = db.query(models.Articulo).filter(models.Articulo.slug == slug).first()
        
        if not existing_article:
            # Si no existe, el slug es único y podemos usarlo.
            return slug
        
        # Si ya existe, incrementamos el contador y creamos un nuevo slug
        counter += 1
        slug = f"{base_slug}-{counter}"