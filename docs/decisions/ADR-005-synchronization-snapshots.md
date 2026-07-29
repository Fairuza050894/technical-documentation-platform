# ADR-005: Synchronization Runs as Catalog Snapshots

## Status

Accepted.

## Decision

Every successful OpenAPI synchronization creates an immutable run identity. Normalized operations and schemas are linked to that run and the source checksum.

The current catalog is derived from the latest completed run for each source. Historical runs remain available for the upcoming change-detection slice.

The first implementation executes synchronously within the application process. The application service depends only on parser, artifact-reader, and repository ports, allowing a durable background worker to replace the invocation mechanism later.

## Consequences

- Catalog facts remain traceable to a source checksum and JSON Pointer.
- Failed runs are recorded without replacing the latest successful catalog.
- Change detection can compare run snapshots.
- Large-scale worker orchestration remains intentionally deferred.
