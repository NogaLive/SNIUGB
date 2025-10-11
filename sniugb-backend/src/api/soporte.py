from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from typing import List
import os

from src.utils.security import get_current_user, get_db
from src.models.database_models import Usuario, ContenidoAyuda, SolicitudSoporte, UserRole
from src.models.soporte_models import ContenidoAyudaResponseSchema, SolicitudSoporteCreateSchema
from src.services.notification_service import send_new_support_ticket_notification

soporte_router = APIRouter(
    prefix="/soporte",
    tags=["Ayuda y Soporte"],
    route_class=APIRoute
)

@soporte_router.get("/contenido", response_model=List[ContenidoAyudaResponseSchema])
async def get_contenido_ayuda(db: Session = Depends(get_db)):
    """
    Obtiene todo el contenido de ayuda (FAQs y Videos). Es un endpoint público.
    """
    return db.query(ContenidoAyuda).order_by(ContenidoAyuda.orden).all()

@soporte_router.post("/solicitudes", status_code=status.HTTP_201_CREATED)
async def create_solicitud_soporte(
    solicitud_data: SolicitudSoporteCreateSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea una nueva solicitud de soporte y notifica al administrador."""
    if current_user.rol != UserRole.GANADERO:
        raise HTTPException(status_code=403, detail="Esta función es solo para usuarios ganaderos.")

    nueva_solicitud = SolicitudSoporte(
        **solicitud_data.model_dump(),
        usuario_dni=current_user.numero_de_dni
    )
    db.add(nueva_solicitud)
    db.commit()
    
    admin_email = os.getenv("SUPPORT_EMAIL_ADDRESS")
    if admin_email:
        send_new_support_ticket_notification(
            admin_email=admin_email,
            user_name=current_user.nombre_completo,
            user_dni=current_user.numero_de_dni,
            ticket_category=solicitud_data.categoria,
            ticket_message=solicitud_data.mensaje
        )
    
    return {"message": "Tu solicitud de soporte ha sido enviada con éxito."}