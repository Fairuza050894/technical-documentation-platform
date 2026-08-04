# User Journeys

| Field | Value |
|---|---|
| Document ID | TDP-PROD-003 |
| Status | Controlled draft |
| Owner | Product Management and User Experience |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Journey 1 — Establish project documentation scope

**Actor:** Technical Writer or Project Maintainer

1. Select a Workspace.
2. Create or open a Project.
3. Register Features or Modules.
4. Inspect each feature's deterministic documentation baseline.
5. Identify required documents that are missing, planned, or available.
6. Continue to evidence intake.

**Current support:** Implemented through Workspace, Project, Feature Registry, and Documentation Map.

## Journey 2 — Convert OpenAPI evidence into a reviewed document

**Actor:** Technical Writer

1. Import an OpenAPI file into the selected Project.
2. Synchronize the source into a normalized catalog snapshot.
3. Compare snapshots when a baseline exists.
4. Generate a Technical Source Overview.
5. Preview and download the immutable version.
6. Submit the version for review.
7. Address a change request by generating a new version.
8. Approve or supersede within the current local-development boundary.

**Current support:** Implemented. Production approval remains blocked by missing OIDC and RBAC.

## Journey 3 — Review change impact

**Actor:** Reviewer

1. Open the Project Workbench.
2. Inspect completed synchronization snapshots.
3. Review deterministic breaking and potentially breaking changes.
4. Compare document versions by stable sections.
5. submit a review decision with a comment where required.

**Current support:** Implemented for local MVP.

## Journey 4 — Govern requirements and versions

**Actor:** Analyst, Technical Writer, Reviewer

1. Create a requirement.
2. issue immutable revisions.
3. link the requirement to a Feature and evidence.
4. create a canonical Change Set.
5. calculate feature and document impact.
6. calculate the required semantic version.
7. review any policy override.
8. generate affected documents.

**Current support:** Planned.

## Journey 5 — Release an approved documentation package

**Actor:** Authorized Approver or Release Manager

1. Verify identity and role.
2. confirm all required documents are approved.
3. validate release eligibility.
4. create a release record and export package.
5. preserve checksums, policy versions, and approval evidence.

**Current support:** Planned.
