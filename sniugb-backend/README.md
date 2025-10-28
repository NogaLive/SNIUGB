
# SNIUGB Backend (FastAPI)

Backend profesional para el Sistema Nacional de Identificación Única de Ganado Bovino (SNIUGB).

## Características clave
- FastAPI + SQLAlchemy 2.x + Pydantic v2
- JWT (access + refresh) con **revocación persistente**
- Versionado de API: `/api/v1`
- CORS configurable por entorno
- Sanitización de HTML en publicaciones (Bleach)
- Notificaciones sin efectos colaterales en `GET` (usa `PATCH`)
- Calendario con `PATCH` idempotente para `es_completado`
- Scheduler APScheduler con guardas (evita instancias duplicadas)
- **Prometheus** `/metrics`, **Sentry** opcional, **logging estructurado**
- **Rate limiting** con SlowAPI en endpoints sensibles
- **Alembic** listo + script `scripts/init_db.py` que genera la **migración inicial** autogenerada si no existe
- `Dockerfile` + `docker-compose.yml`
- CI (GitHub Actions): lint, type-check, alembic (offline), tests
- Makefile, Ruff/Mypy configs, `.env.example`

## Puesta en marcha (local)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # configura valores
python scripts/init_db.py   # genera migración inicial y aplica
python seed.py
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

## Con Docker
```bash
docker compose up --build
# API en http://localhost:8000, Métricas en /metrics
```

## Variables de entorno principales
Ver `.env.example`.

## Tests
```bash
pytest -q
```

## Estilo
- Lint: `ruff check .` | Formato: `ruff format .` | Tipado: `mypy src`

## Seguridad
- JWT secreto en `JWT_SECRET`
- Refresh tokens con JTI y revocación
- Rate limiting en login/reset y consulta DNI
- Sanitización HTML en publicaciones
```

