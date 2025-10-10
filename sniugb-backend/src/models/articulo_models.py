from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ArticuloBaseSchema(BaseModel):
    titulo: str
    resumen: str
    contenido_html: str
    imagen_principal: str
    categoria: str

class ArticuloCreateSchema(ArticuloBaseSchema):
    pass

class ArticuloResponseSchema(ArticuloBaseSchema):
    id: int
    fecha_publicacion: datetime
    
    model_config = ConfigDict(from_attributes=True)