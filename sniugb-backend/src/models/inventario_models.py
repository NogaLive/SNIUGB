from pydantic import BaseModel, Field
from typing import Optional

# NOTA:
# - No importamos clases de SQLAlchemy aquí (como Categoria o Catalogo) para evitar
#   errores de Pydantic v2. Trabajaremos con strings/IDs simples.
# - En la base, InventarioItem ahora tiene FK a Catalogo (grupo='INVENTARIO_CATEGORIA').
# - En los schemas exponemos `categoria_nombre` para que el front no tenga que manejar IDs.

class InventarioItemBase(BaseModel):
    nombre_item: str = Field(..., min_length=1)
    descripcion: Optional[str] = None
    stock: int = 0
    unidad_medida: Optional[str] = None
    cantidad_alerta: Optional[int] = None

class InventarioItemCreateSchema(InventarioItemBase):
    # El front envía el texto de la categoría que el usuario seleccionó/creó
    categoria_nombre: Optional[str] = None  # si viene None, el backend podría dejarla sin categoría
    predio_codigo: str

class InventarioItemUpdateSchema(BaseModel):
    nombre_item: Optional[str] = None
    descripcion: Optional[str] = None
    stock: Optional[int] = None
    unidad_medida: Optional[str] = None
    cantidad_alerta: Optional[int] = None
    categoria_nombre: Optional[str] = None  # permite cambiar de categoría

class InventarioItemResponseSchema(InventarioItemBase):
    id: int
    predio_codigo: str
    # Mostramos el nombre de la categoría (derivado de Catalogo) en vez de un objeto SQLA
    categoria_nombre: Optional[str] = None

    model_config = {
        "from_attributes": True  # habilita mapeo desde atributos ORM (Pydantic v2)
    }