from pydantic import BaseModel, ConfigDict
from src.models.database_models import InventarioCategoria


class InventarioItemCreateSchema(BaseModel):
    nombre_item: str
    categoria: InventarioCategoria
    descripcion: str | None = None
    stock: int
    unidad_medida: str

class InventarioItemUpdateSchema(BaseModel):
    nombre_item: str | None = None
    descripcion: str | None = None
    stock: int | None = None
    unidad_medida: str | None = None

class InventarioItemResponseSchema(BaseModel):
    id: int
    nombre_item: str
    categoria: InventarioCategoria
    descripcion: str | None
    stock: int
    unidad_medida: str
    predio_codigo: str

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
    )