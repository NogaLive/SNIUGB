from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect
import pandas as pd
import io

from src.utils.security import get_current_user, get_db
from src.models.database_models import (
    Usuario, Animal, EventoSanitario, 
    EventoProduccion, InventarioItem, Predio
)
from src.models.reporte_models import ReporteCreateSchema

reportes_router = APIRouter(prefix="/reportes", tags=["Reportes"])

TABLAS_MAP = {
    "animales": Animal,
    "eventos_sanitarios": EventoSanitario,
    "eventos_produccion": EventoProduccion,
    "inventario": InventarioItem,
}

@reportes_router.post("/generar")
async def generar_reporte(
    reporte_data: ReporteCreateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera un reporte dinámico con filtros y tipos de datos inteligentes,
    asegurando que el usuario solo acceda a su propia información.
    """
    modelo_principal = TABLAS_MAP.get(reporte_data.tabla_principal)
    if not modelo_principal:
        raise HTTPException(status_code=400, detail="La tabla principal no es válida.")

    query = db.query(modelo_principal)
    
    # Lógica de propiedad: asegurarse de que el usuario solo vea sus datos
    if reporte_data.tabla_principal == 'animales':
        query = query.join(Animal.predio).filter(Predio.propietario_dni == current_user.numero_de_dni)
    elif reporte_data.tabla_principal == 'inventario':
        query = query.join(InventarioItem.predio).filter(Predio.propietario_dni == current_user.numero_de_dni)
    elif reporte_data.tabla_principal in ['eventos_sanitarios', 'eventos_produccion']:
        query = query.join(Animal).join(Predio).filter(Predio.propietario_dni == current_user.numero_de_dni)

    mapper = inspect(modelo_principal)
    for filtro in reporte_data.filtros:
        if not hasattr(modelo_principal, filtro.columna):
            raise HTTPException(status_code=400, detail=f"La columna de filtro '{filtro.columna}' no existe.")
        
        columna = getattr(modelo_principal, filtro.columna)
        tipo_columna = mapper.columns[filtro.columna].type.python_type
        
        valor = filtro.valor
        try:
            if tipo_columna is int: valor = int(valor)
            elif tipo_columna is float: valor = float(valor)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"El valor '{valor}' no es válido para la columna '{filtro.columna}'.")

        if filtro.operador == 'es_igual_a':
            query = query.filter(columna == valor)
        elif filtro.operador == 'contiene' and tipo_columna is str:
            query = query.filter(columna.ilike(f"%{valor}%"))
        elif filtro.operador == 'mayor_que':
            query = query.filter(columna > valor)
        elif filtro.operador == 'menor_que':
            query = query.filter(columna < valor)

    resultados = query.all()

    for col in reporte_data.columnas:
        if not hasattr(modelo_principal, col):
            raise HTTPException(status_code=400, detail=f"La columna '{col}' no es válida para la tabla seleccionada.")

    data_list = [{col: getattr(row, col) for col in reporte_data.columnas} for row in resultados]
    
    if reporte_data.formato == 'json':
        return data_list
    
    df = pd.DataFrame(data_list)
    
    if reporte_data.formato == 'csv':
        stream = io.StringIO()
        df.to_csv(stream, index=False)
        return StreamingResponse(
            iter([stream.getvalue()]), 
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=reporte.csv"}
        )

    if reporte_data.formato == 'xlsx':
        stream = io.BytesIO()
        df.to_excel(stream, index=False)
        return StreamingResponse(
            iter([stream.getvalue()]), 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=reporte.xlsx"}
        )