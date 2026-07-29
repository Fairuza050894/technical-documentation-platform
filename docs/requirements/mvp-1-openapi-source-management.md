# MVP 1 — OpenAPI Source Management

## Objective

Allow a non-technical user to import a structured OpenAPI file into an existing project and receive a validated, source-backed registry record.

## Functional requirements

1. The user can select an existing project.
2. The user can upload an OpenAPI JSON, YAML, or YML file.
3. The platform validates UTF-8 encoding and JSON/YAML syntax.
4. The platform accepts OpenAPI 3.0.x and 3.1.x only.
5. The platform extracts title, API version, path count, and operation count deterministically.
6. The platform records the original file name and SHA-256 checksum.
7. The platform stores uploaded bytes outside the relational database.
8. Source names are unique per project, case-insensitively.
9. Archived projects cannot receive new sources.
10. The user can list, open through the API, and archive source records.

## Non-functional requirements

- Uploaded files are never executed.
- The default maximum file size is 5 MiB.
- Invalid specifications use the standard error envelope.
- Domain and application layers remain independent from FastAPI, SQLite, and YAML libraries.
- UI states include loading, empty, validation error, backend error, and archived states.
