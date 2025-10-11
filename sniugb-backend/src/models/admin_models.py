from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List


# --- Esquemas para Razas y Departamentos (Mantenemos estos) ---
class RazaCreateUpdateSchema(BaseModel):
    nombre: str
    digito_especie: str

class RazaResponseSchema(BaseModel):
    id: int
    nombre: str
    digito_especie: str
    model_config = ConfigDict(from_attributes=True)

class DepartamentoResponseSchema(BaseModel):
    id: int
    nombre: str
    codigo_ubigeo: str
    model_config = ConfigDict(from_attributes=True)

class DepartamentoCreateUpdateSchema(BaseModel):
    nombre: str
    codigo_ubigeo: str

# --- NUEVOS ESQUEMAS PARA ARTÍCULOS (La versión correcta y completa) ---

# Esquema para el Autor (para anidarlo en el artículo)
class AutorSchema(BaseModel):
    numero_de_dni: str
    nombre_completo: str
    model_config = ConfigDict(from_attributes=True)

# Esquema para la Categoría (usado para anidar y para la respuesta de /categorias)
class CategoriaSchema(BaseModel):
    id: int
    nombre: str
    # La imagen_url ya no es necesaria para la respuesta de /articulos, pero la mantenemos
    # por si el endpoint de /categorias la necesita.
    imagen_url: str | None = None
    model_config = ConfigDict(from_attributes=True)

# Esquema para crear/actualizar categorías (Mantenemos este)
class CategoriaCreateUpdateSchema(BaseModel):
    nombre: str

# Esquema principal para mostrar un Artículo en el frontend
class ArticuloSchema(BaseModel):
    id: int
    slug: str
    titulo: str
    resumen: str
    imagen_thumbnail_url: str # Usamos el nombre de campo corregido de la base de datos
    vistas: int
    
    # Aquí anidamos los esquemas de autor y categoría
    categoria: CategoriaSchema
    autor: AutorSchema

    model_config = ConfigDict(from_attributes=True)

# Esquema para la respuesta paginada que el frontend espera
class ArticulosResponse(BaseModel):
    articulos: List[ArticuloSchema]
    total: int
    page: int
    pages: int