# ADR-009: Structured document version comparison

## Status

Accepted.

## Context

Document lifecycle versions are immutable Markdown artifacts. Reviewers need to understand how
one generated version differs from another without relying on an AI summary or an unstable raw
line diff. Generated Technical Source Overviews already use stable level-two sections such as API
summary, endpoint catalog, component schemas, and breaking-change summary.

## Decision

The platform compares versions from the same document series by parsing level-two Markdown
headings. Each section receives a normalized key and SHA-256 checksum. The comparator emits
`ADDED`, `MODIFIED`, or `REMOVED` section changes with before and after checksums and bounded
plain-text evidence excerpts.

The comparison is computed on demand and is not persisted in MVP 1. Exact document versions and
checksums remain the source of truth. Duplicate section keys are rejected because an ambiguous
mapping would weaken deterministic traceability.

## Consequences

- Formatting changes inside a section remain visible as a modified section.
- Section comparison is stable and independent of UI rendering.
- Reviewers receive bounded evidence without exposing runtime files.
- Comparison does not claim semantic equivalence and does not use AI.
- Future document types must preserve unique level-two headings or provide their own comparator.
