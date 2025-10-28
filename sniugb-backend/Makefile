
.PHONY: install dev migrate seed run lint type test up down fmt

install:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

dev:
	uvicorn server:app --reload --host 0.0.0.0 --port 8000

migrate:
	alembic upgrade head

seed:
	python seed.py

run:
	uvicorn server:app --host 0.0.0.0 --port 8000

lint:
	ruff check .

fmt:
	ruff format .

type:
	mypy src

test:
	pytest -q

up:
	docker compose up --build

down:
	docker compose down -v
