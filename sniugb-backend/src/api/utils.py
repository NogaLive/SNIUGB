from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from src.utils.limiter import limiter
from src.services.reniec_service import get_data_from_reniec
from src.utils.security import get_db
from src.models.database_models import Raza, Departamento

utils_router = APIRouter(
    prefix="/utils",
    tags=["Utilidades"],
    route_class=APIRoute,
)

# Modelo simple para las respuestas de las listas
class SimpleResponse(BaseModel):
    nombre: str

@utils_router.get("/consulta-dni/{dni}")
@limiter.limit("10/minute")
async def consulta_dni(
    dni: str,
    request: Request,  # requerido por SlowAPI
):
    """
    Endpoint para consultar el nombre completo asociado a un DNI.
    """
    if not dni or not dni.isdigit() or len(dni) != 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El DNI debe tener 8 dígitos numéricos.")

    data = get_data_from_reniec(dni)

    if data and data.get("nombre_completo"):
        return {"nombre": data["nombre_completo"]}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró información para el DNI proporcionado.")

@utils_router.get("/razas", response_model=List[SimpleResponse])
async def get_razas(db: Session = Depends(get_db)):
    """
    Obtiene la lista de todas las razas de ganado disponibles en la base de datos.
    """
    razas = db.query(Raza.nombre).order_by(Raza.nombre).all()
    return [{"nombre": raza[0]} for raza in razas]

@utils_router.get("/departamentos", response_model=List[SimpleResponse])
async def get_departamentos(db: Session = Depends(get_db)):
    """
    Obtiene la lista de todos los departamentos del Perú disponibles en la base de datos.
    """
    departamentos = db.query(Departamento.nombre).order_by(Departamento.nombre).all()
    return [{"nombre": departamento[0]} for departamento in departamentos]
