from contextlib import asynccontextmanager
import os
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

# Observabilidad / seguridad
import structlog
import sentry_sdk
from prometheus_fastapi_instrumentator import Instrumentator

# Rate limiting
from src.utils.limiter import limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

# Handlers de error uniformes
from src.utils import error_handler

# Routers
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

# Scheduler
from src.jobs.scheduler import scheduler, setup_jobs

# =========================
# Configuración base
# =========================
API_PREFIX = "/api/v1"
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")]
STATIC_DIR = Path(os.getenv("STATIC_DIR", "static"))
FAVICON_PATH = STATIC_DIR / "ico" / "Logo_gob.ico"

def setup_logging() -> None:
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    )
    logging.basicConfig(level=logging.INFO)

# Sentry (opcional)
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=float(os.getenv("SENTRY_TRACES", "0.2")))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Arranque
    if not scheduler.running:
        setup_jobs()
        scheduler.start()
    try:
        yield
    finally:
        # Apagado
        if scheduler.running:
            scheduler.shutdown()

# Inicializa logging antes de crear la app
setup_logging()

# =========================
# FastAPI app
# =========================
app = FastAPI(
    title="SNIUGB API",
    description="API para el Sistema Nacional de Identificación Única de Ganado Bovino",
    version="1.0.0",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)

# Rate limit: middleware + handler
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
def ratelimit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"error": {"code": "RATE_LIMIT", "message": "Rate limit exceeded"}}
    )

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static (si lo usas)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Favicon (definir DESPUÉS de crear app)
if FAVICON_PATH.exists():
    @app.get("/Logo_gob.ico", include_in_schema=False)
    async def favicon():
        resp = FileResponse(str(FAVICON_PATH), media_type="image/x-icon")
        resp.headers["Cache-Control"] = "public, max-age=86400"
        return resp

# Routers (versionados)
app.include_router(auth_router,           prefix=API_PREFIX)
app.include_router(users_router,          prefix=API_PREFIX)
app.include_router(utils_router,          prefix=API_PREFIX)
app.include_router(predios_router,        prefix=API_PREFIX)
app.include_router(animales_router,       prefix=API_PREFIX)
app.include_router(transferencias_router, prefix=API_PREFIX)
app.include_router(inventario_router,     prefix=API_PREFIX)
app.include_router(dashboard_router,      prefix=API_PREFIX)
app.include_router(notificaciones_router, prefix=API_PREFIX)
app.include_router(reportes_router,       prefix=API_PREFIX)
app.include_router(calendario_router,     prefix=API_PREFIX)
app.include_router(admin_router,          prefix=API_PREFIX)
app.include_router(publicaciones_router,  prefix=API_PREFIX)
app.include_router(soporte_router,        prefix=API_PREFIX)
app.include_router(categorias_router,     prefix=API_PREFIX)

# Prometheus (¡después de crear app!)
Instrumentator().instrument(app).expose(app)

@app.get("/", tags=["Health Check"])
def root():
    return {"message": "Bienvenido a la API de SNIUGB. El sistema está operativo."}

# Handlers de error uniformes
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
app.add_exception_handler(StarletteHTTPException, error_handler.http_exception_handler)
app.add_exception_handler(RequestValidationError, error_handler.validation_exception_handler)

@app.exception_handler(Exception)
async def all_exceptions(request, exc):
    return await error_handler.unhandled_exception_handler(request, exc)

@app.options("/{path:path}")
def preflight_handler():
    return {}