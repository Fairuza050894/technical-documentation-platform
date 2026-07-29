# MVP 1 — Documents Workspace

## Objective

Expose immutable document versions and the lifecycle core through one professional workspace for
technical writers, reviewers, and approvers.

## Functional requirements

1. Users can generate a version with an actor and revision reason.
2. Identical generated content reuses the existing checksum-backed version.
3. Version history shows version number, status, snapshot, revision reason, actor, and timestamp.
4. Users can preview and download any immutable version.
5. Valid lifecycle actions are shown according to version status.
6. Request changes requires a review comment.
7. Workflow history shows actor, action, status, comment, and timestamp.
8. The current version and current approved version are visually distinguishable.
9. Two versions in the same document series can be compared.
10. Comparison changes are filterable by `ADDED`, `MODIFIED`, and `REMOVED`.
11. Comparison evidence includes section excerpts and checksums.
12. Versions from different document series cannot be compared.

## Non-functional requirements

- Comparison is deterministic and does not use AI.
- Existing document generation and lifecycle APIs remain backward compatible.
- Document content stays immutable.
- Empty states and invalid transitions provide clear feedback.
- Keyboard-accessible native controls are used for forms and actions.
- All backend and frontend quality gates must pass.
