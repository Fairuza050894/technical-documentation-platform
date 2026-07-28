# Coding Standards

## Backend

- Python 3.12.
- Type hints are required for public functions and methods.
- Ruff handles formatting and linting.
- Mypy runs in strict mode.
- Pydantic models validate external boundaries only.
- Domain entities protect invariants and do not depend on frameworks.
- Stable error codes are required for expected failures.
- Structured logs must not include credentials or secret values.

## Frontend

- TypeScript strict mode.
- React components use explicit props and accessible HTML semantics.
- Avoid `any`; justify unavoidable exceptions locally.
- Keep remote server state separate from transient UI state.
- Use internal design tokens instead of ad-hoc values.
- Do not use color as the only status indicator.
- Avoid decorative charts, gradients, glassmorphism, excessive radius, and generic AI-product language.

## General

- Prefer composition over inheritance.
- Keep changes small and independently reviewable.
- Tests should assert behavior, not implementation details.
- Comments explain decisions or constraints, not obvious syntax.
