# Document Control

| Field | Value |
|---|---|
| Document ID | TDP-GOV-002 |
| Status | Controlled draft |
| Owner | Technical Documentation and Quality |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Control metadata

Controlled documents under product, governance, quality, compliance, operations, releases, security, and user-guide directories require:

```text
Document ID
Status
Owner
Classification
Review cadence
Source of truth
```

The documentation generator rejects missing or duplicate Document IDs.

## Lifecycle states

| State | Meaning |
|---|---|
| Controlled draft | Maintained in Git and ready for review, but not formally authorized |
| Reviewed | Content review completed by the named reviewer |
| Approved | Authorized by the accountable organizational role |
| Superseded | Replaced by a newer controlled document |
| Retired | No longer applicable and retained for history |

Repository commit or merge does not automatically mean formal organizational approval.

## Change control

- changes are reviewed through Git diff;
- material architecture changes require an ADR;
- material product changes require PRD and flow updates;
- generated indexes are updated only through the generator;
- approval evidence must identify the role, scope, decision, and effective version.

## Versioning

Repository documents use Git history as the current version record. Formal document versions may be introduced when organizational release governance is approved.

Generated application documents use the platform's document lifecycle and are separate from repository-document versioning.

## Review cadence

Cadence is event-driven unless a document specifies otherwise. Triggering events include:

- material code or schema changes;
- new external integrations;
- security-boundary changes;
- release preparation;
- audit finding or incident;
- standards-profile change.
