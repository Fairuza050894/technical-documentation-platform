# Product Requirements Document

| Field | Value |
|---|---|
| Document ID | TDP-PRD-001 |
| Status | Controlled draft |
| Owner | Product Management and Technical Documentation |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## 1. Purpose

Define the canonical product intent, scope, stakeholders, capabilities, constraints, and release boundaries for the Technical Documentation Platform.

## 2. Product objective

Provide a governed engineering-documentation workspace in which business intent is revisioned, technical facts are derived from verifiable evidence, changes are classified deterministically, impact obligations are calculated by policy, and document review can be audited.

## 3. Primary stakeholders

- Technical Writers;
- Business and System Analysts;
- Software Engineers;
- Quality Engineers;
- Reviewers and Approvers;
- Engineering Managers;
- Security, Risk, and Compliance stakeholders;
- Platform Administrators.

Detailed needs are maintained in [Stakeholders and personas](stakeholders-and-personas.md).

## 4. Canonical product workflow

The project workbench follows one governed chain:

```text
Workspace
→ Project
→ Feature or Module
→ Requirement Revision
→ Source Intake
→ Evidence Snapshot
→ Change Set
→ Impact Assessment
→ Document Version
→ Review / Approval
→ Release
```

A stage may recommend the next action, but it must not invent missing facts or silently bypass an upstream governance boundary.

## 5. Current MVP scope

### Implemented

- persistent Workspace and Project boundaries;
- Feature and Module Registry;
- immutable Requirement Registry revisions with explicit owner and change reason;
- verified trace links from a requirement revision to existing Feature, Evidence, and Document records;
- traceability coverage calculation based only on verified links;
- OpenAPI file import with checksum-backed artifact storage;
- canonical Evidence Artifact, Materialization, and Claim primitives with source provenance and checksums;
- normalized API catalog snapshots;
- deterministic comparison of API operations and schemas;
- deterministic change-impact policy that calculates requirement review, test execution, and document review obligations;
- Technical Source Overview generation plus governed enterprise document-profile foundations;
- template registry and customization workflow;
- immutable document versions;
- workflow history, review, approval, supersession, and comparison;
- verified-identity separation-of-duties policy preventing an author from approving the same document version;
- server-resolved identity boundary, with a controlled local-development identity for evaluation;
- repository scanner with real repository analysis, tests, lint, dependency/security scans, comparisons, and SonarQube integration;
- liveness, readiness, security headers, CI, dependency auditing, secret scanning, and repository quality gates.

### Partial / controlled foundation

- requirement traceability is available for Feature, Evidence, and Document targets; broader test-case and release trace targets remain future extensions;
- canonical evidence currently has strongest deterministic acquisition for OpenAPI and governed references; repository-scanner findings are not automatically promoted into official evidence;
- change impact is deterministic for normalized API catalog changes; broader DB, IaC, CI/CD, and runtime impact policies remain future profiles;
- document separation of duties is enforced for verified identities; full enterprise RBAC and workspace membership authorization remain production-readiness work;
- template management is implemented, while generic evidence-to-template generation coverage is still being expanded;
- SQLite and local artifact storage remain development/evaluation adapters.

### Planned before enterprise pilot

- OIDC production configuration, RBAC, workspace membership administration, and role-specific permissions;
- explicit versioned database migrations and PostgreSQL production persistence;
- release/export packages with manifest, checksums, approval record, and traceability summary;
- audit views for requirement revisions, impact decisions, and approval exceptions;
- formal observability, backup, recovery, retention, and deployment controls;
- end-to-end accessibility validation and formal security assessment.

### Future extensions

- CI/CD, IaC, container, database, environment, and runtime evidence collectors;
- secure remote evidence acquisition;
- test-case and UAT trace targets;
- CLI;
- read-only and governed MCP tools;
- API conformance testing;
- data-pipeline and Debezium documentation.

## 6. Functional capability groups

| Capability ID | Capability | Current state |
|---|---|---|
| CAP-001 | Workspace and project governance | Implemented for local MVP |
| CAP-002 | Feature or module registry | Implemented |
| CAP-003 | Evidence source management | OpenAPI and governed references implemented |
| CAP-004 | Evidence normalization, provenance, and snapshots | Implemented foundation; OpenAPI strongest profile |
| CAP-005 | Deterministic change detection | API catalog implemented |
| CAP-006 | Document generation | Technical Source Overview implemented; enterprise profiles expanding |
| CAP-007 | Document lifecycle and comparison | Implemented |
| CAP-008 | Requirement revisions and traceability | Implemented foundation |
| CAP-009 | Deterministic impact policy | API catalog impact policy implemented |
| CAP-010 | Template and document-profile management | Template registry implemented; profile coverage expanding |
| CAP-011 | Verified identity and authorization | Identity + approval SoD foundation implemented; production RBAC planned |
| CAP-012 | Release and export governance | Planned |
| CAP-013 | Automation adapters | CLI and MCP planned |
| CAP-014 | Repository analysis | Implemented as scanner subsystem; official-evidence promotion controlled |

## 7. Business rules

1. Requirement edits create immutable revisions; prior revisions remain auditable.
2. A trace link is marked verified only after its target exists inside the same project boundary.
3. A changed requirement revision does not automatically inherit prior evidence links; the new revision must be re-verified.
4. Equivalent normalized technical inputs and policy versions must yield deterministic comparison and impact results.
5. Breaking API changes require requirement review and expanded documentation/test obligations.
6. AI may summarize or recommend, but may not create an official fact, verified trace, impact decision, or approval without deterministic/source-backed evidence.
7. A verified identity may not approve a document version it authored. The local development identity is an explicit non-production evaluation exception.
8. Archived projects/workspaces remain readable but reject new governed lifecycle mutations.

## 8. Quality attributes

### Traceability

Every generated factual statement must be attributable to immutable evidence or explicitly marked unavailable. Requirements, evidence, change impact, and document versions must preserve stable identifiers and revision history.

### Determinism

Equivalent normalized inputs and policy versions must produce equivalent outputs, impact obligations, and checksums.

### Security

Identity must be resolved by the server. Secrets and prohibited data must never be embedded in generated documents or repository logs. Production approval must honor separation of duties.

### Maintainability

Domain rules remain framework-independent. Frontend and backend modules must be independently testable. Product stages must reuse canonical services instead of maintaining duplicate business rules in the UI.

### Accessibility

User-facing functionality targets WCAG 2.2 Level AA practices, subject to formal testing before release.

### Portability

Environment-specific values are externalized. Production deployment packaging remains planned.

## 9. Success measures

The following measures will be baselined before pilot; numeric targets require product-owner approval:

- percentage of active requirements with verified feature, evidence, and document traceability;
- percentage of generated factual statements linked to evidence;
- percentage of required documents with an assigned owner and lifecycle state;
- time from evidence change to recorded impact assessment;
- time from impact detection to reviewed document update;
- deterministic regeneration success rate;
- stale-document detection rate;
- quality-gate pass rate;
- escaped documentation defects;
- approval separation-of-duties violations prevented;
- accessibility defects by severity.

## 10. Constraints

- SQLite and local artifact storage are development adapters only.
- The local identity provider is prohibited in staging and production.
- Current normalized technical evidence and impact parsing are strongest for OpenAPI/API catalog data.
- Repository scanner findings are advisory until explicitly promoted into canonical evidence through a governed adapter.
- Current official output is Markdown.
- Current routing and UI are optimized for desktop technical work.
- Formal legal, security, compliance, or standards certification is outside the authority of this repository.

## 11. Release acceptance

A release candidate must satisfy the [Release readiness](../releases/release-readiness.md) checklist, pass `make verify`, have current generated documentation, and have documented residual risks. Enterprise releases must also demonstrate verified identity controls and no unresolved separation-of-duties violation.

## 12. Change control

Material changes to product scope, stakeholder obligations, evidence semantics, traceability rules, security boundaries, impact policy, or release criteria require a reviewed update to this PRD and, when architectural, an ADR.
