# MVP 1 Requirement: Technical Source Overview

## Objective

Generate a traceable Markdown overview from a completed normalized OpenAPI synchronization snapshot.

## Functional requirements

1. A user selects an active project and a completed target synchronization.
2. A user may select a different completed baseline synchronization.
3. The system generates Markdown containing:
   - project metadata;
   - source and OpenAPI metadata;
   - synchronization identity and checksum;
   - API operation summary;
   - parameters, request bodies, and responses;
   - component schemas and properties;
   - security schemes and tags;
   - JSON Pointer evidence;
   - deterministic breaking-change summary when a baseline is selected;
   - generation policy and traceability notes.
4. The system stores generation history.
5. A user can preview a generated document.
6. A user can download Markdown with its stable file name.
7. The API exposes a SHA-256 checksum for the generated content.

## Deterministic rules

- Operations are ordered by path and method.
- Schemas are ordered by name.
- Tags, security schemes, media types, and references are ordered.
- Generation time and random document ID are not embedded in Markdown.
- Missing descriptions are stated explicitly.
- No AI-generated facts are permitted.

## API contract

```text
POST /api/projects/{project_id}/documents/technical-source-overview
GET  /api/projects/{project_id}/documents
GET  /api/documents/{document_id}
GET  /api/documents/{document_id}/download
```

## Acceptance criteria

- Repeated generation from the same snapshots yields identical Markdown and checksum.
- Invalid, missing, cross-project, or incomplete snapshots are rejected.
- Preview and download return the stored Markdown.
- Quality gates and the dedicated document-generation audit pass.
