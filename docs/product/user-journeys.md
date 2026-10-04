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
4. Inspect project readiness and the documentation baseline.
5. Identify missing requirements, evidence, or required documents.
6. Continue to governed intent and evidence intake.

**Current support:** Implemented through Workspace, Project, Feature Registry, Project Workbench, and documentation readiness views.

## Journey 2 — Govern business and system intent

**Actor:** Business Analyst, System Analyst, Product Owner, or Technical Writer

1. Create a requirement with type, owner, statement, acceptance criteria, and change reason.
2. Map the requirement to an existing Feature when implementation ownership is known.
3. Create a new immutable revision when the requirement changes.
4. Add verified trace links to canonical Evidence and Document records.
5. Review traceability coverage before treating downstream documentation as complete.

**Current support:** Implemented foundation. Requirement revisions are immutable and trace targets are accepted only after same-project verification. Test-case and release trace targets remain future extensions.

## Journey 3 — Convert technical sources into canonical evidence

**Actor:** Technical Writer, Engineer, or Project Maintainer

1. Import an OpenAPI source or register a governed semantic evidence reference.
2. Synchronize supported technical sources into normalized snapshots.
3. Register source and catalog artifacts as canonical Evidence.
4. For semantic referenced evidence, submit a typed manifest for deterministic materialization.
5. Create observed or deterministically inferred Claims only when their evidence rules are satisfied.
6. Preserve provenance, checksum, collector identity, and capture time.

**Current support:** Implemented foundation. OpenAPI/API catalog is the strongest automated profile. User Journey, Deployment Runtime, and UAT Result are governed referenced-evidence profiles. Repository Scanner findings remain advisory until a governed promotion adapter exists.

## Journey 4 — Review deterministic change impact

**Actor:** Analyst, Engineer, QA, Technical Writer, or Reviewer

1. Select completed baseline and target synchronization snapshots.
2. Compare normalized operations and schemas.
3. Review breaking and potentially breaking changes.
4. Calculate deterministic impact obligations.
5. Confirm whether requirement review and test execution are required.
6. Review the document profiles identified by policy.
7. Use traceability and evidence views to complete the required downstream work.

**Current support:** Implemented for normalized API catalog changes. DB, IaC, CI/CD, and runtime-specific impact policies remain controlled extensions.

## Journey 5 — Generate, review, and approve governed documentation

**Actor:** Technical Writer, Reviewer, or Approver

1. Generate or reuse an immutable document version from supported evidence.
2. Inspect provenance and version history.
3. Submit a Draft for review.
4. Request changes with a required reason, or approve an In Review version.
5. For verified identities, enforce separation of duties so an author cannot approve their own version.
6. When a newer approved version replaces an older approved version, preserve supersession history.

**Current support:** Implemented for the current document lifecycle. Production approval remains bounded by incomplete enterprise RBAC/workspace-membership administration.

## Journey 6 — Analyze repository health without inventing official facts

**Actor:** Engineer, QA, DevOps, Technical Writer, or Engineering Manager

1. Start a Repository Scanner run.
2. Inspect detected stack, tests, lint results, dependency/security findings, and SonarQube metrics when configured.
3. Compare scanner runs and review documentation suggestions.
4. Treat scanner findings as advisory analysis.
5. Promote findings into official evidence only through a governed evidence adapter when one is available.

**Current support:** Scanner implemented. Automatic promotion into canonical evidence is intentionally not implemented.

## Journey 7 — Release an approved documentation package

**Actor:** Authorized Approver or Release Manager

1. Verify identity, authorization, and separation-of-duties conditions.
2. Confirm required documents are approved and traceability obligations are satisfied.
3. Validate release eligibility.
4. Create a release/export package with manifest, checksums, approvals, and traceability summary.
5. Preserve the release record for audit and recovery.

**Current support:** Planned before enterprise pilot. Release/export governance is not represented as completed functionality.
