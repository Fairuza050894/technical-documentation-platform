SHELL := /bin/bash

.PHONY: help bootstrap dev-backend dev-frontend lint test build verify audit audit-projects audit-sources audit-catalog audit-changes audit-documents audit-lifecycle audit-documents-workspace audit-product-ui audit-visual-refinement audit-workbench audit-workspaces audit-features

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
	  '  make audit          Write the foundation audit to Downloads' \
	  '  make audit-projects Write the Project Management audit to Downloads' \
	  '  make audit-sources  Write the OpenAPI Source audit to Downloads' \
	  '  make audit-catalog  Write the API Catalog audit to Downloads' \
	  '  make audit-changes  Write the Change Detection audit to Downloads' \
	  '  make audit-documents Write the document generator audit to Downloads' \
	  '  make audit-lifecycle Write the document lifecycle audit to Downloads' \
	  '  make audit-documents-workspace Write the Documents Workspace audit to Downloads' \
	  '  make audit-product-ui Write the Product UI audit to Downloads' \
	  '  make audit-visual-refinement Write the visual refinement audit to Downloads' \
	  '  make audit-workbench Write the Project Workbench audit to Downloads' \
	  '  make audit-workspaces Write the Workspace Foundation audit to Downloads' \
	  '  make audit-features Write the Feature / Module Registry audit to Downloads'

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


audit-projects:
	bash scripts/audit_project_management.sh


audit-sources:
	bash scripts/audit_openapi_sources.sh


audit-catalog:
	bash scripts/audit_api_catalog.sh


audit-changes:
	bash scripts/audit_change_detection.sh


audit-documents:
	bash scripts/audit_document_generator.sh


audit-lifecycle:
	bash scripts/audit_document_lifecycle.sh


audit-documents-workspace:
	bash scripts/audit_documents_workspace.sh


audit-product-ui:
	bash scripts/audit_product_ui.sh


audit-visual-refinement:
	bash scripts/audit_visual_refinement.sh


audit-workbench:
	bash scripts/audit_project_workbench.sh


audit-workspaces:
	bash scripts/audit_workspace_foundation.sh


audit-features:
	bash scripts/audit_feature_module_registry.sh
