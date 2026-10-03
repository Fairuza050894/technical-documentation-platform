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

Provide a governed documentation workspace in which technical facts are derived from evidence, requirements are versioned immutably, changes are classified deterministically, impacts are traceable, and human review decisions can be audited.

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
- canonical Evidence Artifact and Claim contracts with provenance, checksum, classification, and deterministic derivation rules;
- normalized API catalog snapshots;
- deterministic comparison of API operations and schemas;
- immutable Requirement Revisions with append-only revision history;
- explicit trace links from requirement revisions to features, evidence, documents, tests, and changes;
- deterministic impact assessment for mapped and unmapped changes;
- human-governed impact workflow states and immutable workflow events;
- Technical Source Overview generation;
- immutable document versions;
- document workflow history, review, approval, supersession, and comparison;
- document template registry and customization workflow;
- Repository Scanner with real test, lint, dependency-security analysis, scan comparison, webhook intake, and optional SonarQube evidence;
- server-resolved local development identity plus OIDC/JWT foundations;
- workspace membership, authorization-policy, and audit-log foundations;
- liveness, readiness, security headers, CI, and dependency scanning;
- repository quality and documentation freshness gates.

### Planned before pilot

- project UI for Requirement, Traceability, Impact, and workflow queues;
- canonical cross-source Change Set contract shared by API, repository, database, CI, and runtime collectors;
- deterministic document-version decision policy driven by approved impact assessments;
- generic document profiles and typed metric contracts beyond the current enterprise generation profiles;
- production OIDC/RBAC policy completion and separation-of-duties enforcement on governance mutations;
- explicit schema migrations and production persistence;
- release governance, approved export packages, retention, backup, and recovery controls.

### Future extensions

- CI/CD, IaC, container, database, environment, and runtime evidence collectors;
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
| CAP-003 | Evidence source management | OpenAPI plus governed referenced evidence implemented |
| CAP-004 | Evidence normalization and snapshots | Canonical evidence contract implemented; additional collectors planned |
| CAP-005 | Deterministic change detection | API catalog and scanner comparison implemented |
| CAP-006 | Document generation | Technical Source Overview and enterprise profile foundation implemented |
| CAP-007 | Document lifecycle and comparison | Implemented |
| CAP-008 | Requirement revisions | Implemented as immutable, append-only revisions |
| CAP-009 | Traceability and deterministic impact | Implemented for explicit trace links and governed impact assessments; automatic document-version decision remains planned |
| CAP-010 | Template and document-profile management | Template registry implemented; generic evidence/profile expansion remains planned |
| CAP-011 | Verified identity and authorization | Local/OIDC/JWT/membership foundations implemented; production SoD enforcement planned |
| CAP-012 | Release and export governance | Planned |
| CAP-013 | Automation adapters | CLI and governed MCP planned |
| CAP-014 | Repository engineering evidence | Scanner, security/test/lint evidence and SonarQube integration implemented |
| CAP-015 | Governance decision workflow | Impact review state machine and audit events implemented; configurable enterprise workflow remains planned |

## 6. Enterprise governance chain

The canonical operating model is:

```text
Workspace
→ Project
→ Feature / Module
→ Requirement Revision
→ Evidence / Engineering Target
→ Trace Link
→ Change
→ Impact Assessment
→ Human Review Decision
→ Document Update / Verification Action
→ Document Review
→ Release
```

Rules:

1. A requirement revision is immutable after creation; a change creates a new revision.
2. A factual claim must remain source-backed according to the Evidence domain rules.
3. Impact assessment derives only from explicit trace links and deterministic policy.
4. An unmapped change is surfaced for triage rather than silently treated as safe.
5. An impact assessment cannot transition directly from `OPEN` to `APPROVED`.
6. Every workflow transition records server-resolved actor identity and an immutable event.
7. AI may recommend mappings or summaries but may not create official facts or approve a decision.

## 7. Quality attributes

### Traceability

Every generated fact must be attributable to immutable evidence or explicitly marked as unavailable. Requirement, evidence, implementation, verification, documentation, and change relationships must be representable as explicit trace links.

### Determinism

Equivalent normalized inputs, trace links, and policy versions must produce equivalent impact actions and equivalent generated outputs.

### Security

Identity must be resolved by the server. Secrets and prohibited data must never be embedded in generated documents or repository logs. Production governance mutations require policy enforcement and separation of duties before pilot approval.

### Maintainability

Domain rules remain framework-independent. Frontend and backend modules must be independently testable. Governance domain code must not depend on HTTP or persistence adapters.

### Accessibility

User-facing functionality targets WCAG 2.2 Level AA practices, subject to formal testing before release.

### Portability

Environment-specific values are externalized. Production deployment packaging remains planned.

## 8. Success measures

The following measures will be baselined before pilot; targets require product-owner approval:

- percentage of generated statements linked to evidence;
- percentage of active requirements with implementation and verification trace links;
- percentage of detected changes with a completed impact decision;
- percentage of unmapped changes triaged within the agreed SLA;
- percentage of required documents with an assigned owner and lifecycle state;
- time from evidence change to reviewed document update;
- deterministic regeneration success rate;
- stale-document detection rate;
- quality-gate pass rate;
- escaped documentation defects;
- accessibility defects by severity.

## 9. Constraints

- SQLite and local artifact storage are development adapters only.
- The local identity provider is prohibited in staging and production.
- Current first-class parser/normalizer coverage remains strongest for OpenAPI; repository scanner evidence is a parallel engineering-intelligence path and is not yet a universal canonical Change Set.
- Current official output is Markdown.
- Current governance capability is API/domain-first; dedicated Requirement/Impact workbench UX remains before-pilot work.
- Current impact policy operates on explicit trace links; it does not infer undocumented relationships.
- Formal legal, security, and compliance approval is outside the authority of this repository.

## 10. Release acceptance

A release candidate must satisfy the [Release readiness](../releases/release-readiness.md) checklist, pass `make verify`, have current generated documentation, and have documented residual risks.

## 11. Change control

Material changes to product scope, stakeholder obligations, security boundaries, governance state transitions, trace semantics, impact policy, or release criteria require a reviewed update to this PRD and, when architectural, an ADR.
