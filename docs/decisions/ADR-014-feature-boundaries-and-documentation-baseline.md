# ADR-014 — Feature Boundaries and Deterministic Documentation Baseline

## Status

Accepted.

## Context

Workspace and Project boundaries are established, but documentation remains directly scoped to
Project. The platform needs a stable Feature or Module identity before requirement revisions,
source evidence, impacts, and document versions can be related consistently.

The existing `documents` table is unique by `(project_id, document_type)`. Rebuilding that table
now would combine two concerns: introducing Feature boundaries and changing the mature document
lifecycle.

## Decision

Create an independent `features` module and additive SQLite tables:

- `features`
- `feature_documentation_map`

Feature keys are unique inside a Project. The documentation map stores a versioned policy key,
required/optional classification, and an optional future `document_id` link. Existing documents
and versions are unchanged.

The initial policy is deterministic and based on capability kind. It does not use AI and does not
allow subjective version or coverage selection.

## Consequences

- Feature identity can be referenced by future Requirement, Change Set, and Impact modules.
- Existing source, catalog, change, and document APIs remain project-scoped.
- Coverage starts as policy-derived intent rather than claiming that project documents are
  already feature-specific.
- A later additive migration can link document series to features after impact and version
  policies are defined.
