import os
from pathlib import Path
from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_DIR = ROOT / "alembic"
VERSIONS_DIR = ALEMBIC_DIR / "versions"
INI_PATH = ROOT / "alembic.ini"
ENV_PATH = ALEMBIC_DIR / "env.py"

ENV_PY_CONTENT = """from __future__ import annotations
from alembic import context
from logging.config import fileConfig
import os, sys
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
from src.config.database import engine
from src.models.database_models import Base
target_metadata = Base.metadata
def run_migrations_offline():
    url = str(engine.url)
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()
def run_migrations_online():
    connectable = engine
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""

INI_CONTENT = """[alembic]
script_location = alembic
[loggers]
keys = root,sqlalchemy,alembic
[handlers]
keys = console
[formatters]
keys = generic
[logger_root]
level = WARN
handlers = console
[logger_sqlalchemy]
level = WARN
handlers = console
qualname = sqlalchemy.engine
[logger_alembic]
level = INFO
handlers = console
qualname = alembic
[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic
[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
"""

def ensure_alembic_scaffold():
    ALEMBIC_DIR.mkdir(parents=True, exist_ok=True)
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
    if not INI_PATH.exists():
        INI_PATH.write_text(INI_CONTENT, encoding="utf-8")
    if not ENV_PATH.exists():
        ENV_PATH.write_text(ENV_PY_CONTENT, encoding="utf-8")

def ensure_initial_revision():
    cfg = Config(str(INI_PATH))
    # Si no hay archivos en versions, crea la revisión inicial
    if not any(VERSIONS_DIR.glob("*.py")):
        command.revision(cfg, message="initial", autogenerate=True)
    command.upgrade(cfg, "head")

if __name__ == "__main__":
    ensure_alembic_scaffold()
    ensure_initial_revision()
