# ADR-004: Local artifact storage for the proof of concept

## Status

Accepted for MVP 1.

## Decision

Uploaded technical source files are stored under `.runtime/artifacts` through an `ArtifactStore` port. The domain stores only a safe relative artifact key and a SHA-256 checksum.

## Rationale

- Keeps the proof of concept lightweight while local disk space is constrained.
- Avoids storing source file bytes in SQLite.
- Allows a future S3 or MinIO adapter without changing the application use case.
- Preserves traceability to the exact imported bytes.

## Controls

- Only `.json`, `.yaml`, and `.yml` files are accepted in this slice.
- Maximum file size is 5 MiB by default.
- File names are reduced to a safe base name.
- Files are never executed.
- Artifact keys cannot be absolute or contain parent traversal.
- SHA-256 is calculated from the original uploaded bytes.
