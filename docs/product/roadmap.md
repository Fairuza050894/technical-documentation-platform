# Product Roadmap

| Field | Value |
|---|---|
| Document ID | TDP-PROD-005 |
| Status | Controlled draft |
| Owner | Product Management and Engineering |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Enterprise core baseline — 2026-10-03

The product is now managed as an evidence-backed engineering and documentation control plane, not as a collection of independent utilities.

| Phase | Outcome | State |
|---|---|---|
| 1 | Product and information architecture consolidated around Workspace → Project → Feature → Source/Evidence → Change → Governance → Document | Complete at product/domain baseline; dedicated Governance workbench UI remains before pilot |
| 2 | Canonical evidence foundation with provenance, checksums, observed/inferred claim rules, and governed references | Complete foundation; broader collectors remain roadmap |
| 3 | Immutable Requirement Revisions and explicit traceability relationships | Complete backend/domain/API foundation |
| 4 | Deterministic Change Impact assessment with explicit unmapped-change triage | Complete backend/domain/API foundation |
| 5 | Human-governed Impact workflow with state transition validation and immutable workflow events | Complete backend/domain/API foundation |

“Complete foundation” means the capability has executable domain rules, persistence/API composition, tests, and controlled documentation. It does not mean the platform is production approved.

## Current product chain

```text
Workspace
→ Project
→ Feature / Module
→ Requirement Revision
→ Evidence / Engineering Target
→ Trace Link
→ Change
→ Impact Assessment
→ Human Decision
→ Required Documentation / Verification Action
→ Document Lifecycle
→ Release
```

## Next sequence

| Sequence | Initiative | Outcome |
|---|---|---|
| E6 | Document Profile Engine | Make document types explicit contracts over evidence, requirement, and approved impact inputs |
| E7 | Enterprise Governance UX | Project-local Requirements, Traceability Matrix, Impact Inbox, review timeline, and clear next-action UX |
| E8 | Production Readiness | PostgreSQL+migrations, production OIDC/RBAC/SoD, observability, backup/recovery, deployment packaging, retention |
| E9 | Enterprise Pilot | Dogfood one real repository/project from evidence acquisition through reviewed documentation update |
| E10 | Canonical Cross-Source Change Set | Unify API, repository, DB, CI/CD, IaC, and runtime changes behind a stable change contract |
| E11 | Secure Remote Evidence Acquisition | Allowlisted, redacted, immutable, and auditable remote evidence |
| E12 | Automation Adapters | CLI, read-only MCP, then governed mutation adapters after authorization maturity |
| Later | Data/Runtime Documentation | Kafka Connect, Debezium, Schema Registry, monitoring and runtime relationship evidence |

## Document-profile sequence

| Document type | Planned mode | Prerequisite |
|---|---|---|
| As-Built Documentation | Deterministic evidence generation | Canonical evidence + approved impact inputs |
| Low Level Design | Deterministic plus governed additions | API/schema/code/configuration evidence |
| High Level Design | Hybrid | Requirement + ADR + architecture evidence and human rationale |
| Installation Guide | Evidence-driven | CI/CD, IaC, container and environment evidence |
| SOP | Governed structured authoring | Template registry, roles, review and approval |
| User Guide | Governed structured authoring | Verified UI/task evidence, review and approval |
| Project Handover | Compilation and readiness | Latest approved documents, open-item register, owners and sign-off |

## Automation sequence

```text
Stable domain/application services
        ↓
CLI presentation adapter
        ↓
Read-only MCP
        ↓
OIDC + RBAC + membership + separation of duties
        ↓
Governed MCP mutations / agent adapters
```

## Guardrails

- Official facts require source evidence or explicit unavailable status.
- AI may recommend trace links, explanations, or summaries but cannot silently create official facts.
- Agentic approval, publication, policy mutation, and release mutation are prohibited until production identity/authorization and separation of duties exist.
- An impact decision must use explicit trace relationships; an unmapped change is triaged, never treated as no impact.
- Requirement revisions remain append-only.
- Workflow approval must pass through the defined review state; direct approval shortcuts are prohibited.
- Remote acquisition remains prohibited until SSRF, allowlist, credential-reference, timeout, rate, isolation, and redaction controls exist.
- New document types must use generic evidence/document-profile contracts.
- Project Handover compiles approved content and must not silently include drafts.
- Browser-agent testing supplements but never replaces deterministic regression tests.
- Live conformance execution remains separate from `make verify`.
- Visual polish must not obscure evidence provenance, state, ownership, or next action.
