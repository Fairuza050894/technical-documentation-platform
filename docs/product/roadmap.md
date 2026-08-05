# Product Roadmap

| Field | Value |
|---|---|
| Document ID | TDP-PROD-005 |
| Status | Controlled draft |
| Owner | Product Management and Engineering |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Roadmap policy

Sequence is based on architectural prerequisites and risk reduction. Dates are not committed in this document.

| Sequence | Initiative | Outcome |
|---|---|---|
| 0009.11 | Documentation Governance and Living Repository Docs | Canonical project documentation and CI freshness |
| 0009.12 | Frontend Composition and CSS Foundation | Completed foundation: composed app shell and ordered CSS responsibility |
| 0009.13 | Requirement Registry and Structured Revisions | Stable requirement identity and history |
| 0009.14 | Generic Evidence and Document Profile Foundation | Evidence snapshots and reusable document profiles |
| 0009.15 | Reusable Composition Root and CLI | Safe automation without duplicating business rules |
| 0010 | Canonical Change Set and Version Policy | Deterministic impact and version decisions |
| 0011 | Static DevOps Documentation Pilot | CI/CD, IaC, container, and environment profiles |
| 0012 | Secure Remote Evidence Acquisition | Allowlisted, redacted, auditable remote evidence |
| 0013 | OIDC, RBAC, and Release Governance | Verified identity and separation of duties |
| 0014 | Agentic and Conformance Pilot | Read-only MCP, governed generation, sandbox conformance |
| 0015 | Data Pipeline Documentation | Kafka Connect, Debezium, topics, and schemas |
| Later | Production persistence and deployment | PostgreSQL, migrations, packaging, backup, observability |

## Guardrails

- Agentic approval is prohibited until verified identity and authorization exist.
- Remote acquisition is prohibited until SSRF and credential controls exist.
- New document types must use generic evidence and document-profile contracts.
- Mobile and dark mode remain secondary to governance, security, and maintainability.
