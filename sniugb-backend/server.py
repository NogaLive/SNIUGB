from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# --- Importaciones de Routers ---
from src.api.auth import auth_router
from src.api.users import users_router
from src.api.utils import utils_router
from src.api.predios import predios_router
from src.api.animales import animales_router
from src.api.transferencias import transferencias_router
from src.api.inventario import inventario_router
from src.api.dashboard import dashboard_router
from src.api.notificaciones import notificaciones_router
from src.api.reportes import reportes_router
from src.api.calendario import calendario_router
from src.api.admin import admin_router
from src.api.publicaciones import publicaciones_router
from src.api.soporte import soporte_router
from src.api.categorias import categorias_router
from src.api.chatbot import chatbot_router


# --- Importaciones del Scheduler ---
from src.jobs.scheduler import scheduler, setup_jobs

# --- Lógica de Ciclo de Vida (Lifespan) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando aplicación y tareas programadas...")
    setup_jobs()
    scheduler.start()
    yield
    print("Apagando tareas programadas y aplicación...")
    scheduler.shutdown()

# --- Creación de la Aplicación FastAPI ---
app = FastAPI(
    title="SNIUGB API",
    description="API para el Sistema Nacional de Identificación Única de Ganado Bovino",
    version="1.0.0",
    lifespan=lifespan
)

# --- Configuración de CORS ---
origins = [
    "http://localhost:4200",  # Dirección estándar de Angular
    "http://127.0.0.1:4200", # Alternativa para algunos navegadores
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Montaje de Archivos Estáticos ---
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Inclusión de todos los Routers ---
app.include_router(chatbot_router) # Sin prefijo para un webhook más limpio
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
app.include_router(categorias_router, prefix="/api")

@app.get("/", tags=["Health Check"])
def root():
    return {"message": "Bienvenido a la API de SNIUGB. El sistema está operativo."}