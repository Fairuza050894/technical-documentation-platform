# Stakeholders and Personas

| Field | Value |
|---|---|
| Document ID | TDP-PROD-002 |
| Status | Controlled draft |
| Owner | Product Management and User Experience |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Stakeholder groups

| Stakeholder | Primary interest | Decision rights |
|---|---|---|
| Product Owner | Product value, scope, roadmap | Product priority and acceptance |
| Technical Documentation | Accuracy, usability, document governance | Documentation structure and content quality |
| Engineering | Source integrity, architecture, maintainability | Technical design and implementation |
| Reviewers | Evidence sufficiency and change clarity | Review disposition |
| Approvers | Organizational authorization | Approval and release, once RBAC exists |
| Security and Compliance | Control effectiveness and risk | Control acceptance and exceptions |
| Platform Operations | Reliability, backup, recovery | Operational readiness |
| End users | Efficient discovery and trusted documentation | Usability feedback |

## Primary personas

### Technical Writer

**Goals**

- understand project and feature scope;
- identify missing required documents;
- generate source-backed documentation;
- compare versions and respond to review comments.

**Pain points**

- inconsistent input formats;
- undocumented changes;
- unclear ownership;
- manual reconciliation across tools.

### System or Business Analyst

**Goals**

- capture requirements and acceptance criteria;
- connect requirements to features and evidence;
- review impact before release.

**Current limitation**

The Requirement Registry is planned and is not yet implemented.

### Software Engineer

**Goals**

- provide source evidence;
- understand documentation impact of code or schema changes;
- avoid duplicating facts manually.

### Reviewer

**Goals**

- inspect evidence and change summaries;
- request corrections with a recorded rationale;
- verify that a new version addresses prior comments.

### Approver

**Goals**

- authorize a reviewed version within assigned scope;
- preserve a defensible approval trail.

**Current limitation**

Production OIDC, RBAC, and separation of duties are not yet implemented. Local-development approval is not non-repudiation.

### Platform Administrator

**Goals**

- configure workspaces, integrations, policies, templates, and access;
- monitor system readiness and audit evidence.

**Current limitation**

Administrative access control and connector management are roadmap items.
