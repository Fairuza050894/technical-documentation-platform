SHELL := /bin/bash

.PHONY: help bootstrap dev-backend dev-frontend lint test build verify audit

help:
	@printf '%s\n' \
	  'Available commands:' \
	  '  make bootstrap      Install local development dependencies' \
	  '  make dev-backend    Start FastAPI on http://127.0.0.1:8000' \
	  '  make dev-frontend   Start Vite on http://127.0.0.1:4173' \
	  '  make lint           Run backend and frontend linting' \
	  '  make test           Run backend and frontend tests' \
	  '  make build          Build the frontend and validate backend imports' \
	  '  make verify         Run lint, tests, and build' \
	  '  make audit          Write one audit report to Downloads'

bootstrap:
	bash scripts/bootstrap_macos.sh

dev-backend:
	uv run --project backend uvicorn tdp.main:app --reload --host 127.0.0.1 --port 8000

dev-frontend:
	npm --prefix frontend run dev

lint:
	uv run --project backend ruff check backend
	uv run --project backend ruff format --check backend
	uv run --project backend mypy backend/src
	npm --prefix frontend run lint

test:
	uv run --project backend pytest backend/tests
	npm --prefix frontend run test

build:
	uv run --project backend python -c "from tdp.main import app; assert app.title"
	npm --prefix frontend run build

verify: lint test build

audit:
	bash scripts/audit_foundation.sh
