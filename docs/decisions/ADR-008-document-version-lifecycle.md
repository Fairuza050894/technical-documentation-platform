# ADR-008: Immutable document versions and auditable lifecycle

- Status: Accepted
- Date: 2026-07-29

## Context

The deterministic generator originally stored each output as an independent history row. MVP 1 requires a stable document identity, immutable versions, duplicate-content protection, review states, approval, and a traceable workflow history.

## Decision

A Technical Source Overview is represented by one document series per project and document type. Each distinct Markdown checksum creates an immutable version. The first version is `1.0`; subsequent distinct content increments the minor number. Identical content returns the existing version.

Versions transition through `DRAFT`, `IN_REVIEW`, `CHANGES_REQUESTED`, `APPROVED`, and `SUPERSEDED`. Workflow transitions are domain-controlled and recorded as immutable events with actor, comment, previous status, new status, and timestamp.

Approving a newer version automatically supersedes the previously approved version. This preserves one current approved version without mutating document content.

The SQLite repository creates lifecycle tables additively and migrates existing deterministic generation history. The legacy table remains untouched as a rollback source.

## Consequences

- Generated content remains immutable and checksum-backed.
- Duplicate generation does not inflate version history.
- Review and approval decisions are auditable.
- Existing local document history is retained.
- The Documents Workspace can be upgraded independently in the next patch.
