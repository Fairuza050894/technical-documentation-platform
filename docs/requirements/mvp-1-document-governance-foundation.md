# MVP 1 — Enterprise Document Governance Foundation

## Objective

Establish a deterministic Project-level Document Type Registry, automation-profile policy, and
minimum Project Documentation Checklist without changing the existing generation workflow.

## Domain boundary

The canonical Project-level registry contains HLD, LLD, As-Built, SOP, User Guide, Installation
Guide, Project Handover, UAT Evidence, Journey Map, and Developer Onboarding Brief.

`TECHNICAL_SOURCE_OVERVIEW` remains a backward-compatible deterministic system artifact. It is not
treated as an enterprise checklist item and does not satisfy another governed Project document by
implication.

The existing Feature/Module `DocumentationType` taxonomy remains a bounded Feature-module concern
in this slice. Future integration must map Feature coverage to Project documents explicitly rather
than equating similarly named enum values silently.

## Automation profiles

- HLD: `HYBRID`
- LLD: `EVIDENCE_DRIVEN`
- As-Built: `EVIDENCE_DRIVEN`
- SOP: `GOVERNED_AUTHORING`
- User Guide: `GOVERNED_AUTHORING`
- Installation Guide: `EVIDENCE_DRIVEN`
- Project Handover: `GOVERNED_BUNDLE`
- UAT Evidence: `EVIDENCE_DRIVEN`
- Journey Map: `EVIDENCE_DRIVEN`
- Developer Onboarding Brief: `HYBRID`

Profiles describe governance and automation intent only. They do not authorize generation.

## Default Project checklist

Policy key: `project-documentation-baseline-v1`.

Required: HLD, LLD, As-Built, SOP, User Guide, Installation Guide, and Project Handover.

Supplementary: UAT Evidence, Journey Map, and Developer Onboarding Brief.

The policy is backend-owned and deterministic. The policy key keeps the contract extensible for
future Workspace- or Project-specific overrides without hardcoded frontend rules.

## Availability semantics

`AVAILABLE` means that at least one persisted version exists for that governed type. It does not
mean approved, publication-ready, evidence-complete, or generation-eligible.

Archived Projects remain readable while existing mutation guards remain unchanged.

## API

Read-only endpoints:

- `GET /api/document-types`
- `GET /api/projects/{project_id}/documentation-checklist`

Frontend checklist integration is deferred to the dedicated workbench integration slice.

## AI boundary

AI does not determine type applicability, required/supplementary policy, checklist availability,
readiness, evidence provenance, version decisions, or approval state.

## Non-goals

No Evidence/Claim entities, confidence model, readiness engine, generation eligibility, template
CRUD, enterprise-document generator, checklist UI, AI drafting, Documentation Recovery, MCP, or
live conformance testing is introduced.

## Acceptance criteria

- exactly ten ordered enterprise document types;
- seven required and three supplementary policy items;
- one typed automation profile per registry item;
- Technical Source Overview receives no enterprise checklist credit;
- availability is derived from persisted document versions;
- archived Project checklists remain readable;
- unknown Projects return the existing document-project not-found error;
- Clean Architecture boundaries and current generation behavior remain intact;
- focused tests and `make verify` pass.
