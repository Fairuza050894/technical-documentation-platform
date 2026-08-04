# Control Evidence Matrix

| Field | Value |
|---|---|
| Document ID | TDP-COMP-002 |
| Status | Controlled draft |
| Owner | Security, Quality, and Technical Documentation |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Purpose

Map control objectives to current repository evidence and known gaps.

| Control objective | Current evidence | Gap or next action |
|---|---|---|
| Architecture decisions are controlled | ADR-001 through current ADR, generated ADR index | add formal decision owners consistently |
| Requirements are documented | `docs/requirements/`, PRD, generated requirements index | stable requirement revisions and test linkage |
| Changes are verified | `make verify`, GitHub Actions | branch protection must be configured in GitHub settings |
| Documentation remains current | `make docs-check`, documentation test | human review remains required |
| Identity is not client supplied | ADR-015, identity model and tests | OIDC and RBAC |
| Unsafe local identity fails closed | configuration validation and tests | production identity adapter |
| Security issues have a reporting path | `SECURITY.md` | approved security contact and SLA |
| Dependencies are reviewed | Dependabot | vulnerability severity and exception policy |
| Runtime data stays outside Git | `.gitignore`, audit exclusions | production secret and artifact controls |
| Evidence integrity is protected | checksums, immutable snapshots and versions | generic evidence registry |
| Backup and restore are documented | local backup runbook | scheduled production backup and restore testing |
| Release readiness is controlled | release policy and checklist | verified release role and immutable release record |
| Accessibility is considered | coding standards and component tests | formal WCAG evaluation |
| External recommendations are tracked | audit management response | recurring review and closure evidence |

## Evidence rule

A file path is evidence that a control is designed, not proof that it operates effectively in every environment. Operational effectiveness requires execution records and authorized review.
