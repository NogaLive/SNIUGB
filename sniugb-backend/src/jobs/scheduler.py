from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .expiration_jobs import expire_old_transfer_requests

# Creamos una instancia del programador
scheduler = AsyncIOScheduler()

def setup_jobs():
    """
    Añade todos los trabajos programados al scheduler.
    """
    # Programamos la tarea para que se ejecute cada hora.
    # Puedes ajustar el intervalo a 'minutes=30', 'days=1', etc.
    scheduler.add_job(expire_old_transfer_requests, 'interval', hours=1)
    
    print("Tareas programadas configuradas.")