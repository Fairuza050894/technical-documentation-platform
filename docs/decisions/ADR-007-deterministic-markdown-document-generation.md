# ADR-007: Deterministic Markdown Document Generation

## Status

Accepted.

## Context

The platform already stores normalized synchronization snapshots and deterministic change comparisons. Technical documentation must now be rendered from those records without introducing unsupported facts or losing source evidence.

Generated output must be reproducible, downloadable, and traceable to the exact synchronization snapshot used as input.

## Decision

The first generated document type is `TECHNICAL_SOURCE_OVERVIEW` in Markdown format.

The application service loads:

- project metadata;
- source metadata;
- one completed target synchronization;
- normalized operations and component schemas;
- an optional completed baseline synchronization;
- deterministic comparison results when a baseline is selected.

A replaceable renderer converts that context into Markdown. The renderer sorts operations, schemas, tags, and security schemes and does not include generation time or a random document identifier inside the Markdown. Therefore, identical normalized inputs produce identical content and the same SHA-256 checksum.

Generation history metadata and Markdown content are stored in SQLite for the local MVP. The document record stores the target and optional baseline synchronization identifiers.

## Consequences

- Generated facts remain source-backed.
- JSON Pointer evidence remains visible in the document.
- Repeated generation can be verified by checksum.
- AI is not part of the factual generation path.
- Markdown is the only output format in this slice.
- Large-scale artifact storage and PDF/DOCX rendering remain future concerns.
