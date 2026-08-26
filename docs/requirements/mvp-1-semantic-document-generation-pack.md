# MVP 1 — Semantic Document Generation Pack

## Objective

Generate four enterprise document types deterministically from immutable materialized semantic
Evidence without network resolution, fabricated Source identities, or AI-authored facts.

## Supported profiles

| Document type | Profile | Required materialized evidence |
| --- | --- | --- |
| User Guide | `enterprise-user-guide-v1` | `USER_JOURNEY` |
| Installation Guide | `enterprise-installation-guide-v1` | `DEPLOYMENT_RUNTIME` |
| UAT Evidence | `enterprise-uat-evidence-v1` | `UAT_RESULT` |
| Journey Map | `enterprise-journey-map-v1` | `USER_JOURNEY` |

The existing `enterprise-generation-profile-v2` registry shape is reused because profile metadata
does not require another schema change.

## Eligibility and evidence selection

`document-readiness-v3` remains the only eligibility policy. The generation input adapter selects the
latest matching **materialized** Evidence Artifact deterministically using the existing artifact sort
order. A registered but unmaterialized semantic artifact cannot unlock generation.

The adapter revalidates the persisted canonical manifest and projects it into transport-independent
Documents application facts. The Documents domain does not import Evidence types.

## Deterministic content

### User Guide

Renders journey name, actors, preconditions, ordered steps, expected outcomes, and source references.
It does not invent screens, controls, labels, or navigation.

### Journey Map

Renders the governed journey sequence and outcomes. It does not invent personas, emotions, channels,
pain points, opportunities, or additional stages.

### Installation Guide

Renders environment, runtime component names/versions, prerequisites, configuration **key names**,
deployment steps, verification checks, and rollback references. Configuration values and secrets are
never rendered.

### UAT Evidence

Renders run reference, execution time, scenario ID/title/status, expected result, actual result,
evidence references, and deterministic PASSED/FAILED/BLOCKED counts.

## Provenance and lifecycle

Semantic generated versions have nullable `source_id` and `target_run_id`. Their immutable
`document_version_provenance` contains the selected Evidence Artifact ID, kind, and checksum.

The existing Document Series, checksum idempotency, minor-version progression, review, approval,
download, comparison, and audit lifecycle is reused.

## Frontend

The existing Documents workspace becomes one generic generation entry point. Technical Source
Overview continues to expose target/baseline snapshot controls. Enterprise document types call the
existing generic generation endpoint and let backend readiness/evidence selection remain canonical.

## Safety boundaries

- no external HTTP or local-file resolution;
- no raw Evidence payload copied into Documents persistence;
- no invented deployment, journey, UI, UAT, or architecture facts;
- no configuration values or secret material;
- no AI factual generation;
- no SOP or Project Handover generation in this pack;
- no browser/Vibium, CI/CD collector, live UAT collector, or MCP integration.

## Acceptance criteria

- all four profiles are registered through the existing generic enterprise generation service;
- registered-only semantic evidence remains blocked;
- materialized evidence generates deterministic Markdown;
- source-free provenance is persisted truthfully;
- identical canonical inputs reuse the existing immutable version;
- existing HLD, LLD, As-Built, and Technical Source Overview behavior remains compatible;
- the existing review/download/version lifecycle works for semantic documents;
- frontend exposes the supported generated document types through one generation form;
- focused tests and the complete repository quality gate pass.
