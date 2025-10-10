from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.config.database import engine
import src.models.database_models as db_models
from src.api.chatbot import chatbot_router
from src.api.auth import auth_router
from src.api.users import users_router
from src.api.utils import utils_router
from src.api.predios import predios_router
from src.api.animales import animales_router
from src.api.transferencias import transferencias_router
from src.api.inventario import inventario_router
from src.api.dashboard import dashboard_router
from src.api.notificaciones import notificaciones_router
from src.jobs.scheduler import scheduler, setup_jobs
from src.api.reportes import reportes_router
from src.api.calendario import calendario_router
from src.api.admin import admin_router
from src.api.publicaciones import publicaciones_router
from src.api.soporte import soporte_router

# Crea las tablas en la base de datos si no existen
db_models.Base.metadata.create_all(bind=engine)

origins = [
    "http://127.0.0.1:4200", # La dirección de tu frontend Angular
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código que se ejecuta al iniciar la aplicación
    print("Iniciando aplicación y tareas programadas...")
    setup_jobs()
    scheduler.start()
    yield
    # Código que se ejecuta al apagar la aplicación
    print("Apagando tareas programadas y aplicación...")
    scheduler.shutdown()

# Crea la aplicación FastAPI
app = FastAPI(
    title="SNIUGB API",
    description="API para el Sistema Nacional de Identificación Única de Ganado Bovino",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Permite los orígenes definidos
    allow_credentials=True,
    allow_methods=["*"], # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"], # Permite todas las cabeceras
)

# Incluye las rutas de los diferentes módulos
app.include_router(chatbot_router)
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(utils_router, prefix="/api")
app.include_router(predios_router, prefix="/api")
app.include_router(animales_router, prefix="/api")
app.include_router(transferencias_router, prefix="/api")
app.include_router(inventario_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(notificaciones_router, prefix="/api")
app.include_router(reportes_router, prefix="/api")
app.include_router(calendario_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(publicaciones_router, prefix="/api")
app.include_router(soporte_router, prefix="/api")

@app.get("/", tags=["Health Check"])
def root():
    return {"message": "Bienvenido a la API de SNIUGB. El sistema está operativo."}