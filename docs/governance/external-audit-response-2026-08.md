# External Audit Management Response — August 2026

| Field | Value |
|---|---|
| Document ID | TDP-GOV-004 |
| Status | Controlled draft |
| Owner | Product, Engineering, Security, and Technical Documentation |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Purpose

Record management assessment of externally supplied technical reviews and map accepted findings
to controlled work. This document summarizes the response; the original review remains external
evidence.

## Disposition definitions

| Disposition | Meaning |
|---|---|
| Completed | Verified in the current repository with code or controlled documentation evidence |
| Partially addressed | A safe foundation exists, but the complete control or product capability does not |
| Open | Accepted work that can be planned without an unresolved prerequisite |
| Deferred | Valid work intentionally sequenced after higher-value or higher-risk priorities |
| Dependency-blocked | Accepted work that must not begin until named architectural or security prerequisites exist |
| Not applicable | Does not apply to the current product boundary |

## Current repository reconciliation

The August review predates the latest Engineering Safety, Living Documentation, Feature Registry,
and Frontend Composition slices. Status below is based on repository commit `ed63a81` and must be
re-verified whenever a material implementation changes.

| Area | Current verified state |
|---|---|
| Request identity | Mutation payloads no longer accept a free-text actor; application commands receive a server-resolved principal |
| Authentication boundary | Local principal and environment safety exist; OIDC, RBAC, membership, and separation of duties do not |
| CI and configuration | GitHub Actions runs `make verify`; frontend API configuration and tracked environment examples exist |
| Security baseline | Security headers, liveness, readiness, `SECURITY.md`, and Dependabot exist |
| Repository governance | CODEOWNERS, pull-request guidance, changelog, release governance, ADRs, and generated documentation indexes exist |
| Frontend maintainability | `App.tsx` is a composition root and `globals.css` is an ordered import manifest; large workspace modules still require incremental decomposition |
| Product taxonomy | Runtime remains limited to `OPENAPI_FILE` and `TECHNICAL_SOURCE_OVERVIEW` |
| Agentic interfaces | No product CLI or MCP server exists |
| Live acquisition | No governed outbound evidence acquisition or live conformance execution exists |
| Production readiness | PostgreSQL, versioned migrations, reproducible deployment packaging, backup, observability, and formal licensing remain unresolved |

## Response matrix

| Finding | Assessment | Disposition | Evidence or target |
|---|---|---|---|
| Client-supplied workflow actor | Critical integrity issue | Partially addressed | ADR-015, `RequestPrincipal`, identity tests; OIDC and authorization still required |
| No CI | Reproducibility gap | Completed | `.github/workflows/verify.yml` |
| Hardcoded frontend API URL | Deployment configuration gap | Completed | frontend API configuration and `.env.example` |
| Missing security headers and readiness | Security and operational gap | Completed | middleware and health tests |
| Missing security policy and dependency updates | Vulnerability-governance gap | Partially addressed | `SECURITY.md` and Dependabot exist; vulnerability audit policy remains open |
| Full authentication and authorization | Required before shared use | Open | OIDC, RBAC, membership, and separation of duties |
| SQLite startup migration | Not production-grade change control | Open | versioned migrations and PostgreSQL adapter |
| No containerization | Production parity gap | Dependency-blocked | stable persistence, identity, runtime, and deployment contracts |
| No license decision | Legal governance gap | Dependency-blocked | authorized organizational licensing decision |
| Missing release and changelog governance | Traceability gap | Partially addressed | policy and `CHANGELOG.md` exist; formal release tags have not begun |
| Missing CODEOWNERS and templates | Repository-governance gap | Completed | `.github/` governance files |
| CSS and large frontend components | Maintainability risk | Partially addressed | ADR-017 and architecture tests; workspace-level decomposition continues |
| Dark mode and broad mobile support | Usability enhancement, not core risk | Deferred | after modularization, governance, security, and product validation |
| OpenAPI-specific document core | Limits enterprise document expansion | Open | generic evidence, typed metrics, and document profiles, Sequence 0009.14 |
| HLD, LLD, As-Built, SOP, User Guide, Installation Guide, and Handover | Required enterprise taxonomy | Open | Document Type Registry, applicability policy, checklist, templates, lifecycle, and audit mapping |
| As-Built profile | Best fit for deterministic evidence generation | Dependency-blocked | generic evidence and document-profile foundation |
| LLD profile | Strong fit for API, schema, code, and configuration evidence | Dependency-blocked | generic metrics and evidence contracts |
| HLD profile | Requires evidence plus governed human rationale | Dependency-blocked | registry, hybrid authoring, ADR and requirement evidence |
| Installation Guide | Requires deployment and environment evidence | Dependency-blocked | static DevOps evidence profiles |
| SOP and User Guide | Primarily governed authoring capabilities | Open | structured templates, authoring, review, approval, and maintenance |
| Project Handover | Approved deliverable compilation | Dependency-blocked | approved-document inventory, readiness rules, and bundle export |
| DevOps document profiles | Valuable product expansion | Dependency-blocked | generic evidence and document-profile foundation before Sequence 0011 |
| Live Debezium and operational integrations | Valuable but high security complexity | Dependency-blocked | secure remote acquisition before data-pipeline profile |
| CLI | Lowest-cost automation adapter | Dependency-blocked | reusable application composition root, Sequence 0009.15 |
| MCP | Discoverable agent interface | Dependency-blocked | CLI/application contracts first; authorization before governed mutations |
| Browser-agent testing | Useful exploratory capability | Deferred | one isolated pilot; regression suite remains authoritative |
| OpenAPI live conformance testing | Valuable project evidence | Dependency-blocked | secure outbound policy, execution isolation, and immutable result evidence |

## Enterprise document automation policy

| Document type | Automation mode | Initial direction |
|---|---|---|
| As-Built Documentation | Deterministic evidence generation | First enterprise profile after the generic foundation |
| Low Level Design | Deterministic plus governed additions | Reuse API, schema, code, and configuration evidence |
| High Level Design | Hybrid | Generate verifiable structure; require human rationale and trade-offs |
| Installation Guide | Evidence-driven when deployment sources exist | Derive from CI/CD, IaC, container, environment, and runbook evidence |
| SOP | Governed structured authoring | Do not fabricate human operational procedures |
| User Guide | Governed structured authoring | Use verified UI evidence and human-reviewed task narratives |
| Project Handover | Approved-document compilation | Bundle latest eligible versions, register, open items, owners, and sign-off |

## Agentic and live-execution boundaries

1. CLI, HTTP, and future MCP adapters invoke the same application use cases.
2. CLI does not call internal HTTP endpoints or access infrastructure repositories directly.
3. MCP begins read-only plus governed draft generation.
4. Approval, publication, policy changes, and other governed mutations remain unavailable to
   agents until OIDC, RBAC, membership, and separation of duties exist.
5. Browser-agent tooling is an exploratory pilot and does not replace stable automated tests.
6. Live conformance testing is separate from the platform quality gate and stores sanitized,
   immutable results as project evidence.
7. Remote targets use deny-by-default outbound controls, SSRF protection, allowlisting, timeouts,
   rate limits, credential references, and redaction.
8. Package choices and versions for CLI, MCP, browser automation, and conformance tooling are
   verified at implementation time rather than copied from an external review.

## Management principles

1. Security and identity prerequisites precede agentic mutations.
2. Live responses become sanitized immutable evidence before rendering.
3. Generic metadata remains typed and schema-versioned.
4. External recommendations are not copied blindly; package versions and commands are verified
   when implemented.
5. Every completed response requires code, tests, documentation, and audit evidence.
