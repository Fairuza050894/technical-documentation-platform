# MVP 1 API Catalog Requirements

## Functional requirements

- Synchronize an active OpenAPI source.
- Record synchronization status, timestamps, checksum, counts, and stable errors.
- Normalize HTTP method, path, operation ID, summary, tags, security, parameters, request body, responses, and source pointer.
- Normalize component schemas and their properties.
- Keep previous successful synchronization runs.
- Show the latest successful catalog per source.
- Filter the catalog by project and source.

## Quality requirements

- No source code or OpenAPI document is executed.
- External OpenAPI references are rejected in MVP 1.
- A failed synchronization must not replace the latest successful catalog.
- Domain and application layers must not import FastAPI or SQLite.
- API and UI output must expose source evidence.
