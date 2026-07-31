# MVP 1 — Project Management Requirements

## Purpose

A project is the top-level boundary for technical sources, catalogs, detected changes, and generated documents.

## Functional requirements

### FR-PROJ-001 Create project

The user can create a project with:

- Name
- Stable project key
- Optional description
- Ownership: Personal or Team

The project key is normalized to uppercase and must be unique.

### FR-PROJ-002 List projects

The user can view all projects with their name, key, ownership, workspace assignment, and lifecycle status.

### FR-PROJ-003 View project

The API exposes a single project by its immutable identifier.

### FR-PROJ-004 Archive project

The user can archive an active project after an explicit inline confirmation. Archiving preserves the record and prevents a second archive operation.

### FR-PROJ-005 Persist locally

Project records remain available after the backend process restarts.

## Validation rules

- Project name: 3-80 characters.
- Project key: 2-20 letters, numbers, or hyphens; first character must be a letter.
- Description: maximum 500 characters.
- Duplicate project keys are rejected.
- Invalid request data uses the standard API error envelope.

## Acceptance criteria

- Create, list, get, and archive endpoints are covered by automated tests.
- Domain validation is independent of FastAPI and SQLite.
- The application layer does not import presentation or infrastructure modules.
- The frontend includes loading, empty, error, success, and archive-confirmation states.
- Local runtime data is excluded from source control.
