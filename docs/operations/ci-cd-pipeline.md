# CI/CD Pipeline

| Field | Value |
|---|---|
| Document ID | TDP-OPS-004 |
| Status | Draft |
| Owner | Engineering |
| Classification | Internal project documentation |
| Review cadence | At each pipeline change |
| Source of truth | This repository |

## Current state

Manual build and test. No automated CI/CD pipeline configured yet.

## Local verification

Backend:

    cd backend && python -m pytest

Frontend type check:

    cd frontend && npx tsc --noEmit

Frontend tests:

    cd frontend && npm test

Frontend lint:

    cd frontend && npm run lint

Frontend build:

    cd frontend && npm run build

## Planned pipeline stages

### Stage 1: Validate

- Backend: python -m pytest (221 tests)
- Frontend: npx tsc --noEmit (zero errors)
- Frontend: npx vitest run (57 tests)
- Frontend: npm run lint (zero warnings)
- Documentation: make docs-check (deterministic freshness)

### Stage 2: Build

- Backend: pip install -e .
- Frontend: npm run build (Vite production bundle)

### Stage 3: Deploy

- Backend: uvicorn with gunicorn workers
- Frontend: Static file serving via reverse proxy

## Quality gates

| Gate | Tool | Threshold |
|---|---|---|
| Type safety | tsc --noEmit | Zero errors |
| Linting | eslint | Zero warnings |
| Unit tests | vitest / pytest | All passing |
| Architecture fitness | AST-based pytest | Dependency rules pass |
| Documentation freshness | make docs-check | No drift |
| Bundle size | vite build | Monitor, no hard limit yet |

## Planned enhancements

- GitHub Actions workflow for automated validation on pull request
- Preview deployment for frontend changes
- Automated dependency update proposals
- Security vulnerability scanning
- Test coverage reporting with threshold enforcement
