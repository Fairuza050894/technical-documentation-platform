# Documentation Policy

| Field | Value |
|---|---|
| Document ID | TDP-GOV-001 |
| Status | Controlled draft |
| Owner | Technical Documentation and Engineering |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Policy objective

Maintain project documentation as controlled, reviewable, traceable repository content that changes with the system it describes.

## Scope

This policy applies to:

- repository README and contribution guidance;
- product, architecture, requirement, quality, security, compliance, operations, and release documents;
- ADRs;
- generated repository indexes;
- external audit management responses.

It does not govern customer documents generated inside the application. Those will be governed by Template Management and Document Lifecycle capabilities.

## Documentation classes

### Human-governed

Human judgment is authoritative for:

- product intent and priority;
- stakeholder needs;
- requirements and acceptance criteria;
- architecture decisions;
- risks and exceptions;
- standards applicability;
- approval and release decisions.

Automation may validate structure and freshness but must not silently alter meaning.

### Deterministically generated

The repository generator may derive:

- module inventory;
- ADR and requirement indexes;
- API routes;
- frontend routing signals;
- test inventory;
- document register.

Generated files contain a warning and must not be edited directly.

## Change rule

A code change must update documentation when it changes behavior, public contract, architecture, security boundary, operations, user flow, or release eligibility.

## Freshness enforcement

```text
make docs
→ review generated diff
→ make docs-check
→ make verify
→ commit code and documentation together
```

CI checks freshness but never commits changes.

## Truthfulness

- implemented, planned, deferred, and prohibited states must be distinguishable;
- missing facts must be stated as missing;
- standards alignment must not be represented as certification;
- local-development controls must not be represented as production controls.
