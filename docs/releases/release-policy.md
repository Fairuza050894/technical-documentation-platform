# Release Policy

| Field | Value |
|---|---|
| Document ID | TDP-REL-001 |
| Status | Controlled draft |
| Owner | Product, Engineering, Quality, and Release Authority |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Release objectives

A release must be reproducible, traceable to source and documentation, and supported by reviewed verification evidence.

## Versioning

The platform will use semantic versioning when formal release tags begin:

```text
MAJOR — incompatible product or public-contract change
MINOR — backward-compatible capability
PATCH — backward-compatible correction
```

During `0.x`, minor releases may contain substantial evolution, but incompatible changes must still be documented.

Generated project-document versions are governed separately by the future deterministic version policy engine.

## Required release inputs

- approved scope;
- current PRD and architecture;
- current generated repository docs;
- passing CI quality gate;
- migration and rollback plan where applicable;
- security and dependency review;
- operational and backup readiness;
- known limitations and residual risks;
- authorized release decision.

## Release record

A future formal release record should include:

```text
release ID and version
commit and artifact checksums
included changes
migration version
configuration profile
quality evidence
security review
documentation set
approver identity and role
release timestamp
rollback reference
```

## Current state

Git commits and CI provide engineering traceability. Formal immutable release records, signed artifacts, and production authorization are planned.
