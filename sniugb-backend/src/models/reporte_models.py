from pydantic import BaseModel
from typing import List, Literal, Dict, Any

# Define los operadores de filtro permitidos
TipoOperador = Literal['es_igual_a', 'contiene', 'mayor_que', 'menor_que']
TipoTabla = Literal['animales', 'eventos_sanitarios', 'eventos_produccion', 'inventario']
TipoFormato = Literal['json', 'csv', 'xlsx']

class FiltroSchema(BaseModel):
    columna: str
    operador: TipoOperador
    valor: Any

class ReporteCreateSchema(BaseModel):
    tabla_principal: TipoTabla
    columnas: List[str]
    filtros: List[FiltroSchema] = [] # Los filtros son opcionales
    formato: TipoFormato = 'json' # El formato por defecto es JSON