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

Provide a governed documentation workspace in which technical facts are derived from evidence, requirements are revision-controlled, changes are classified deterministically, impact decisions are auditable, and document review can be governed through explicit workflow states.

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
- canonical evidence artifacts and governed claims;
- immutable Requirement Registry revisions;
- requirement-to-feature/evidence/test/document/release/source trace links;
- deterministic change-impact assessment by change surface;
- governed human workflow cases with explicit transition rules;
- Technical Source Overview generation;
- immutable document versions;
- workflow history, review, approval, supersession, and comparison;
- built-in and customizable document templates;
- Repository Scanner with real test, lint, dependency-security, SonarQube, and delta analysis;
- server-resolved local development identity;
- liveness, readiness, security headers, CI, and dependency updates;
- repository quality and audit commands.

### Planned before pilot

- automatic creation of project evidence from Repository Scanner results;
- richer evidence adapters for CI/CD, IaC, database schema, deployment, and runtime telemetry;
- deterministic document version policy driven by impact decisions;
- generic evidence-to-document profile rules beyond the Technical Source Overview;
- OIDC, RBAC, workspace membership, and separation of duties;
- explicit schema migrations and production persistence;
- governed release export packages and release evidence bundles;
- operational observability, retention, backup, and recovery controls.

### Future extensions

- secure remote evidence acquisition;
- CLI;
- read-only and governed MCP tools;
- API conformance testing;
- data-pipeline and Debezium documentation;
- workflow-engine adapter for long-running enterprise orchestration when internal workflow rules are no longer sufficient.

## 5. Functional capability groups

| Capability ID | Capability | Current state |
|---|---|---|
| CAP-001 | Workspace and project governance | Implemented for local MVP |
| CAP-002 | Feature or module registry | Implemented |
| CAP-003 | Evidence source management | OpenAPI and governed reference registration implemented |
| CAP-004 | Evidence normalization and snapshots | OpenAPI catalog + canonical evidence model implemented |
| CAP-005 | Deterministic change detection | API catalog implemented |
| CAP-006 | Document generation | Technical Source Overview implemented |
| CAP-007 | Document lifecycle and comparison | Implemented |
| CAP-008 | Requirement revisions | Implemented for local MVP |
| CAP-009 | Deterministic impact and version policy | Impact policy implemented; automatic version policy planned |
| CAP-010 | Template and document-profile management | Template management implemented; generic profile engine planned |
| CAP-011 | Verified identity and authorization | Foundation implemented; production controls planned |
| CAP-012 | Release and export governance | Workflow foundation implemented; export package planned |
| CAP-013 | Automation adapters | Repository Scanner implemented; CLI and MCP planned |
| CAP-014 | End-to-end traceability | Requirement trace links implemented; automated coverage expansion planned |

## 6. Quality attributes

### Traceability

Every generated fact must be attributable to immutable evidence or explicitly marked as unavailable. Requirement traceability must preserve the stable requirement identity across immutable revisions.

### Determinism

Equivalent normalized inputs and policy versions must produce equivalent outputs and checksums. Impact assessment targets are policy outputs rather than free-form AI conclusions.

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
- requirement traceability coverage percentage;
- percentage of required documents with an assigned owner and lifecycle state;
- time from evidence change to reviewed document update;
- deterministic impact-assessment reproducibility;
- deterministic regeneration success rate;
- stale-document detection rate;
- quality-gate pass rate;
- escaped documentation defects;
- accessibility defects by severity.

## 8. Constraints

- SQLite and local artifact storage are development adapters only.
- The local identity provider is prohibited in staging and production.
- Automated evidence parsing remains primarily OpenAPI-specific; additional evidence kinds can be governed as references.
- Current official output is Markdown.
- Current routing and UI are optimized for desktop technical work.
- Governance workflow is an internal deterministic state machine, not yet a distributed workflow-orchestration engine.
- Formal legal, security, and compliance approval is outside the authority of this repository.

## 9. Release acceptance

A release candidate must satisfy the [Release readiness](../releases/release-readiness.md) checklist, pass `make verify`, have current generated documentation, and have documented residual risks.

## 10. Change control

Material changes to product scope, stakeholder obligations, security boundaries, governance workflow, impact policy, or release criteria require a reviewed update to this PRD and, when architectural, an ADR.
