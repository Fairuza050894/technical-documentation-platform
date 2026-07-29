# ADR-003: Use a local SQLite adapter for the first project slice

- Status: Accepted for local MVP development
- Date: 2026-07-29

## Context

The first business slice needs durable project data, but the current development machine does not yet have Docker or PostgreSQL installed and has limited free disk space. Blocking the vertical slice on infrastructure installation would delay validation of the domain, API, and UI flow.

## Decision

Use SQLite through the Python standard library as a local persistence adapter for the Project module. The application layer depends only on the `ProjectRepository` protocol. SQLite-specific code remains inside the infrastructure layer.

The local database is stored at `.runtime/tdp.sqlite3` and is excluded from Git.

## Consequences

- Project data survives backend restarts during local development.
- No additional runtime dependency or database service is required.
- Clean Architecture boundaries can be tested before a PostgreSQL adapter exists.
- SQLite is not approved as the enterprise production database.
- A PostgreSQL adapter can replace it later without changing the Project domain or use cases.
