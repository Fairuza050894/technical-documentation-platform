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

Provide a governed documentation workspace in which technical facts are derived from evidence, changes are classified deterministically, versions are calculated by policy, and document review can be audited.

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

## 4. Current MVP scope

### Implemented

- persistent Workspace and Project boundaries;
- Feature and Module Registry;
- OpenAPI file import with checksum-backed artifact storage;
- normalized API catalog snapshots;
- deterministic comparison of API operations and schemas;
- Technical Source Overview generation;
- immutable document versions;
- workflow history, review, approval, supersession, and comparison;
- server-resolved local development identity;
- liveness, readiness, security headers, CI, and dependency updates;
- repository quality and audit commands.

### Planned before pilot

- Requirement Registry with immutable revisions;
- canonical evidence and change-set model;
- deterministic impact and version policy engine;
- generic document profiles and metadata;
- template management;
- OIDC, RBAC, workspace membership, and separation of duties;
- explicit schema migrations and production persistence;
- release governance and export packages.

### Future extensions

- repository ingestion;
- CI/CD, IaC, container, environment, and operational document profiles;
- secure remote evidence acquisition;
- CLI;
- read-only and governed MCP tools;
- API conformance testing;
- data-pipeline and Debezium documentation.

## 5. Functional capability groups

| Capability ID | Capability | Current state |
|---|---|---|
| CAP-001 | Workspace and project governance | Implemented for local MVP |
| CAP-002 | Feature or module registry | Implemented |
| CAP-003 | Evidence source management | OpenAPI file implemented |
| CAP-004 | Evidence normalization and snapshots | OpenAPI implemented |
| CAP-005 | Deterministic change detection | API catalog implemented |
| CAP-006 | Document generation | Technical Source Overview implemented |
| CAP-007 | Document lifecycle and comparison | Implemented |
| CAP-008 | Requirement revisions | Planned |
| CAP-009 | Deterministic impact and version policy | Planned |
| CAP-010 | Template and document-profile management | Planned |
| CAP-011 | Verified identity and authorization | Foundation implemented; production controls planned |
| CAP-012 | Release and export governance | Planned |
| CAP-013 | Automation adapters | CLI and MCP planned |

## 6. Quality attributes

### Traceability

Every generated fact must be attributable to immutable evidence or explicitly marked as unavailable.

### Determinism

Equivalent normalized inputs and policy versions must produce equivalent outputs and checksums.

### Security

Identity must be resolved by the server. Secrets and prohibited data must never be embedded in generated documents or repository logs.

### Maintainability

Domain rules remain framework-independent. Frontend and backend modules must be independently testable.

### Accessibility

User-facing functionality targets WCAG 2.2 Level AA practices, subject to formal testing before release.

### Portability

Environment-specific values are externalized. Production deployment packaging remains planned.

## 7. Success measures

The following measures will be baselined before pilot; targets require product-owner approval:

- percentage of generated statements linked to evidence;
- percentage of required documents with an assigned owner and lifecycle state;
- time from evidence change to reviewed document update;
- deterministic regeneration success rate;
- stale-document detection rate;
- quality-gate pass rate;
- escaped documentation defects;
- accessibility defects by severity.

## 8. Constraints

- SQLite and local artifact storage are development adapters only.
- The local identity provider is prohibited in staging and production.
- Current evidence parsing is OpenAPI-specific.
- Current official output is Markdown.
- Current routing and UI are optimized for desktop technical work.
- Formal legal, security, and compliance approval is outside the authority of this repository.

## 9. Release acceptance

A release candidate must satisfy the [Release readiness](../releases/release-readiness.md) checklist, pass `make verify`, have current generated documentation, and have documented residual risks.

## 10. Change control

Material changes to product scope, stakeholder obligations, security boundaries, or release criteria require a reviewed update to this PRD and, when architectural, an ADR.
