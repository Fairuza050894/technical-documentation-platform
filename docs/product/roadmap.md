# Product Roadmap

| Field | Value |
|---|---|
| Document ID | TDP-PROD-005 |
| Status | Controlled draft |
| Owner | Product Management and Engineering |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Phase 2 progress: Core Product Quality

| Week | Focus | Status | Date |
|------|-------|--------|------|
| Week 1 | Error boundary, confirmation dialogs, skip-to-content, list filtering | ✅ Complete | 2026-08-27 |
| Week 2 | Document tabs, print styles, sidebar collapse, ARIA consistency | ✅ Complete | 2026-08-27 |
| Week 3 | Evidence UI, enterprise generation UI, visual diff highlighting | ⏳ Next | — |
| Week 4 | Global search, dependency indicators in stage navigation | ⏳ Planned | — |
| Week 5+ | Testing enhancement, CI/CD, compliance and platform documentation | ⏳ Planned | — |

### Week 1 deliverables
- React Error Boundary at application root (`main.tsx`)
- Reusable ConfirmDialog component (native `<dialog>`)
- Workflow confirmation for approve and supersede document actions
- Planned stages 7 and 8 hidden from ProjectWorkbench
- Skip-to-content accessibility link in AppShell
- Text search filters in Sources, Documents, Catalog, and Features workspaces

### Week 2 deliverables
- DocumentsWorkspace refactored to tabbed navigation (Generate / Versions / Compare)
- Print stylesheet (`@media print`) for clean document printing
- Sidebar collapse toggle with icon-only mode and localStorage persistence
- ARIA landmark labels and loading state roles across all workspaces

## Roadmap policy

Sequence is based on architectural prerequisites and risk reduction. Dates are not committed in
this document. A sequence entry is not permission to bypass its guardrails.

| Sequence | Initiative | Outcome |
|---|---|---|
| 0009.11 | Documentation Governance and Living Repository Docs | Completed foundation: canonical project documentation and CI freshness |
| 0009.12 | Frontend Composition and CSS Foundation | Completed foundation: composed app shell and ordered CSS responsibility |
| 0009.13 | Requirement Registry and Structured Revisions | Stable requirement identity, structured revision evidence, and applicability input |
| 0009.14 | Generic Evidence, Typed Metrics, and Document Profiles | Remove OpenAPI-specific assumptions from the reusable document core |
| 0009.15 | Reusable Application Composition Root and CLI | Safe shell automation without duplicated HTTP or business logic |
| 0010 | Canonical Change Set and Version Policy | Deterministic impact, update requirement, and document-version decisions |
| 0010.1 | Enterprise Document Type Registry and Project Checklist | HLD, LLD, As-Built, SOP, User Guide, Installation Guide, and Handover applicability |
| 0010.2 | As-Built and LLD Profiles | First enterprise evidence-driven profiles |
| 0010.3 | HLD Hybrid and Installation Profiles | Evidence-backed structure with governed human input and deployment evidence |
| 0010.4 | SOP, User Guide, and Handover Workflows | Structured authoring plus approved-document bundle and readiness |
| 0011 | Static DevOps Documentation Pilot | CI/CD, IaC, container, environment, monitoring-rule, and runbook evidence profiles |
| 0012 | Secure Remote Evidence Acquisition | Allowlisted, redacted, immutable, and auditable remote evidence |
| 0013 | OIDC, RBAC, Membership, and Release Governance | Verified identity, authorization, separation of duties, and governed release actions |
| 0014 | Agentic and Conformance Pilot | Read-only MCP, governed generation, browser-agent pilot, and sandbox conformance evidence |
| 0015 | Data Pipeline Documentation | Kafka Connect, Debezium, topics, and schemas |
| Later | Production persistence and deployment | PostgreSQL, versioned migrations, packaging, backup, recovery, metrics, and tracing |

## Document-profile sequence

| Document type | Planned mode | Prerequisite |
|---|---|---|
| As-Built Documentation | Deterministic evidence generation | Generic evidence, typed metrics, change sets, and applicability |
| Low Level Design | Deterministic plus governed additions | API, schema, code, configuration, and generic document profiles |
| High Level Design | Hybrid | Requirement and ADR evidence plus human-owned rationale |
| Installation Guide | Evidence-driven | CI/CD, IaC, container, environment, and verification evidence |
| SOP | Governed structured authoring | Template registry, roles, review, and approval |
| User Guide | Governed structured authoring | Verified UI evidence, task model, review, and approval |
| Project Handover | Compilation and readiness | Latest approved documents, open-item register, owners, and sign-off |

## Automation sequence

```text
Reusable application composition root
        ↓
CLI presentation adapter
        ↓
Read-only and governed-generation MCP

OIDC + RBAC + membership + separation of duties
        ↓
Governed agent mutations

Secure remote evidence acquisition
        ↓
OpenAPI conformance, Debezium, Schema Registry, monitoring, and other live sources
```

## Guardrails

- Agentic approval, publication, policy mutation, and release mutation are prohibited until
  verified identity and authorization exist.
- Remote acquisition is prohibited until SSRF, allowlist, credential-reference, timeout, rate,
  isolation, and redaction controls exist.
- New document types must use generic evidence, typed metrics, and document-profile contracts.
- As-Built and LLD are prioritized before higher-ambiguity generation.
- HLD remains hybrid; SOP and User Guide remain governed authoring rather than unattended factual
  generation.
- Project Handover compiles approved content and must not silently include drafts.
- Browser-agent testing supplements but never replaces the deterministic regression suite.
- Live conformance execution remains separate from `make verify`.
- Mobile and dark mode remain secondary to governance, security, accessibility, and
  maintainability.
