# MVP 1 Enterprise Document Taxonomy and Automation Boundaries

## Purpose

Record the accepted enterprise document taxonomy and the architectural boundaries for CLI,
agentic interfaces, browser automation, and live conformance testing before runtime
implementation begins.

## Current implementation boundary

The current production code supports one uploaded evidence type, `OPENAPI_FILE`, and one generated
document type, `TECHNICAL_SOURCE_OVERVIEW`. Document lifecycle and workflow concepts are reusable,
but source parsing, comparison, rendering, and several document-version metrics remain
OpenAPI-specific.

## Functional requirements

1. The future Document Type Registry recognizes High Level Design (HLD), Low Level Design (LLD),
   As-Built Documentation, Standard Operating Procedure (SOP), User Guide, Installation Guide,
   and Project Handover Documentation.
2. Applicability is determined by explicit Project and Feature or Module policy, not by hardcoded
   navigation or user intuition.
3. Every document profile declares one automation mode:
   - deterministic evidence generation;
   - hybrid evidence and human-authored content;
   - governed structured authoring;
   - approved-document compilation or bundling.
4. As-Built is the first preferred enterprise profile because its authoritative content maps most
   directly to verified implementation evidence.
5. LLD reuses API, schema, code, and configuration evidence after generic metrics and evidence
   contracts are available.
6. HLD remains hybrid because business rationale, trade-offs, and architecture decisions cannot
   be inferred safely from implementation artifacts alone.
7. Installation Guide generation requires deployment, environment, CI/CD, container, or
   infrastructure evidence; missing evidence is reported instead of fabricated.
8. SOP and User Guide are governed through templates, structured authoring, versioning, review,
   and approval. They are not targets for unattended factual generation.
9. Project Handover is an approved-document bundle containing the latest eligible versions,
   document register, outstanding items, ownership, and sign-off evidence.
10. A `tdp` CLI is implemented as a presentation adapter over the same application use cases used
    by HTTP. It must not call internal HTTP endpoints, access repositories directly, or duplicate
    domain rules.
11. CLI commands provide deterministic exit codes and support machine-readable output for safe
    automation.
12. MCP is implemented over the same application boundary after the reusable composition root and
    CLI contracts exist.
13. MCP remains read-only plus governed draft generation until OIDC, RBAC, membership, and
    separation-of-duties controls are implemented.
14. Approval, rejection, publication, policy changes, and other governed mutations are not exposed
    to agents before verified authorization exists.
15. Browser-agent tooling is a limited exploratory or pilot capability and does not replace the
    stable unit, integration, component, architecture, and regression test suite.
16. Live OpenAPI conformance testing is isolated from `make verify`, requires an explicit
    environment target, and stores sanitized results as immutable evidence.
17. Every user-supplied remote target is subject to deny-by-default outbound policy, SSRF
    protection, domain allowlisting, timeout, rate, credential-reference, and redaction controls.
18. Live-source acquisition is a shared infrastructure capability for conformance testing,
    Debezium or Kafka Connect, Schema Registry, monitoring, and future operational integrations.

## Non-functional requirements

- Clean Architecture dependency direction remains enforced;
- domain and application logic remain transport-independent;
- no agentic interface becomes an alternate source of business rules;
- document profile metadata is typed and schema-versioned;
- secret values are never collected into generated documentation;
- evidence is immutable, checksummed, attributable, and auditable;
- AI may assist drafting but does not determine factual content, applicability, approval, or
  version decisions;
- implementation dependencies and package versions are verified when each capability is built.

## Sequencing constraints

1. Requirement Registry precedes policy-driven applicability.
2. Generic evidence, typed metrics, and document profiles precede enterprise document generation.
3. A reusable composition root precedes CLI.
4. CLI and application contracts precede MCP.
5. Secure remote acquisition precedes conformance testing and live operational sources.
6. OIDC and RBAC precede agentic approval or other governed mutations.
7. Approved document inventory and lifecycle rules precede Project Handover bundling.

## Acceptance criteria

- the external audit response distinguishes completed, partially addressed, open, deferred, and
  dependency-blocked work;
- the roadmap records the enterprise document taxonomy and automation dependencies;
- the current OpenAPI-only implementation boundary is stated explicitly;
- no runtime source, API contract, database schema, or frontend behavior changes in this
  documentation-only slice;
- `make docs`, `make docs-check`, and `make verify` pass;
- the reconciliation audit writes one complete report under `~/Downloads`.
