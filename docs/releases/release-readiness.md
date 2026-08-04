# Release Readiness

| Field | Value |
|---|---|
| Document ID | TDP-REL-002 |
| Status | Controlled draft |
| Owner | Quality and Release Authority |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Repository candidate checklist

- [ ] Scope and acceptance criteria are documented.
- [ ] Relevant ADRs and requirements are current.
- [ ] `make docs-check` passes.
- [ ] `make verify` passes locally.
- [ ] GitHub Actions `Verify` passes.
- [ ] `git diff --check` passes.
- [ ] No runtime data, `.env`, credentials, or customer artifacts are staged.
- [ ] Changelog is updated.
- [ ] Known limitations and residual risks are documented.
- [ ] Rollback or recovery steps are documented.

## Additional production checklist

- [ ] OIDC and RBAC are enabled.
- [ ] Local identity mode is disabled.
- [ ] Database migration is reviewed and tested.
- [ ] Backup and restore test is current.
- [ ] Deployment artifact is immutable and verified.
- [ ] Security assessment and vulnerability review are complete.
- [ ] Monitoring, alerts, and operational ownership are active.
- [ ] Data classification, retention, and legal ownership are approved.
- [ ] Release authority records the decision.

The production checklist cannot be marked complete by CI alone.
