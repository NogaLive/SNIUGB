from pydantic import BaseModel, ConfigDict
from datetime import datetime

# --- Para Razas ---
class RazaCreateUpdateSchema(BaseModel):
    nombre: str
    digito_especie: str

class RazaResponseSchema(BaseModel):
    id: int
    nombre: str
    digito_especie: str
    
    model_config = ConfigDict(from_attributes=True)

# --- Para Departamentos ---
class DepartamentoResponseSchema(BaseModel):
    id: int
    nombre: str
    codigo_ubigeo: str
    
    model_config = ConfigDict(from_attributes=True)

class DepartamentoCreateUpdateSchema(BaseModel):
    nombre: str
    codigo_ubigeo: str

# --- Para Categorías de Artículos ---
class CategoriaSchema(BaseModel):
    id: int
    nombre: str
    imagen_url: str

    model_config = ConfigDict(from_attributes=True)

class CategoriaCreateUpdateSchema(BaseModel):
    nombre: str
    imagen_url: str

# --- Para Publicaciones (Artículos) ---

class ArticuloBaseSchema(BaseModel):
    titulo: str
    resumen: str
    contenido_html: str
    imagen_principal: str
    categoria: str

class ArticuloCreateSchema(ArticuloBaseSchema):
    pass

class ArticuloUpdateSchema(BaseModel):
    titulo: str | None = None
    resumen: str | None = None
    contenido_html: str | None = None
    imagen_principal: str | None = None
    categoria: str | None = None
    estado_publicacion: str | None = None

class ArticuloSchema(ArticuloBaseSchema):
    id: int
    fecha_publicacion: datetime
    
    model_config = ConfigDict(from_attributes=True)