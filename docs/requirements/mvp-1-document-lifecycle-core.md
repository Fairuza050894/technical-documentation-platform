# MVP 1 Requirement: Document Lifecycle Core

## Goal

Provide version identity, duplicate protection, review status, approval, supersession, and workflow audit history for deterministic Technical Source Overview documents.

## Functional requirements

1. The first distinct generated content creates version `1.0` with `DRAFT` status.
2. A new distinct checksum creates the next minor version in the same project document series.
3. Identical content returns the existing version and does not create another database row.
4. Version content, checksum, source snapshot, and baseline snapshot are immutable.
5. A draft can be submitted for review.
6. A version in review can be approved or receive a change request.
7. A change request requires a non-empty reviewer comment.
8. Approving a newer version automatically supersedes the previous approved version.
9. An approved version can also be superseded explicitly.
10. Every generated version and workflow transition records an immutable event.
11. Existing generator history is migrated automatically without deleting the legacy table.
12. Existing preview and Markdown download endpoints remain backward compatible.

## Non-functional requirements

- Domain code must remain framework-independent.
- SQLite writes that combine version and workflow data must be transactional.
- Invalid transitions must return a stable conflict response.
- All identifiers must use UUID validation.
- All quality gates and the dedicated lifecycle audit must pass.
