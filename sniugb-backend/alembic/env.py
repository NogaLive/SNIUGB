from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
from dotenv import load_dotenv

# --- INICIO DE LA CONFIGURACIÓN PERSONALIZADA ---

# 1. Carga las variables de entorno desde el archivo .env
load_dotenv()

# 2. Importa la metadata de tus modelos de SQLAlchemy
#    Esto es crucial para que Alembic sepa qué tablas debe crear/actualizar.
from src.models.database_models import Base
target_metadata = Base.metadata

# --- FIN DE LA CONFIGURACIÓN PERSONALIZADA ---

# esto es la configuración de Alembic por defecto...
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- INICIO DE LA CONFIGURACIÓN DE URL ---

# 3. Construye la URL de la base de datos dinámicamente
def get_url():
    user = os.getenv("user")
    password = os.getenv("password")
    host = os.getenv("host")
    port = os.getenv("port")
    dbname = os.getenv("dbname")
    # Retorna la URL completa, incluyendo el "?sslmode=require"
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode=require"

# 4. Le dice a Alembic que use esta URL
config.set_main_option('sqlalchemy.url', get_url())

# --- FIN DE LA CONFIGURACIÓN DE URL ---

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()