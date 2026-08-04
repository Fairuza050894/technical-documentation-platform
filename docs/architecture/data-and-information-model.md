# Data and Information Model

| Field | Value |
|---|---|
| Document ID | TDP-ARC-005 |
| Status | Controlled draft |
| Owner | Architecture and Data Governance |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Information classes

| Information | Current storage | Integrity control |
|---|---|---|
| Workspace and project metadata | SQLite | Domain validation and foreign keys |
| Feature registry | SQLite | Stable IDs and unique project key |
| Uploaded OpenAPI evidence | Local artifact store | SHA-256 checksum and safe artifact key |
| Normalized API snapshot | SQLite | Immutable synchronization identity |
| Change comparison | Computed from snapshots | Deterministic comparator |
| Document content | SQLite local MVP | Immutable content checksum |
| Workflow events | SQLite | Immutable transition record |
| Repository documentation | Git | Review history and generated freshness checks |

## Current relationship model

```text
Workspace 1 ── * Project
Project   1 ── * Feature
Project   1 ── * Source
Source    1 ── * Synchronization Run
Project   1 ── * Document
Document  1 ── * Document Version
Version   1 ── * Workflow Event
```

## Data integrity principles

- IDs are not regenerated during additive migration.
- Runtime artifacts are never committed to Git.
- Existing evidence relationships are preserved when introducing Workspace and Feature boundaries.
- Document content and history are not overwritten.
- Sensitive fields must be redacted before a future remote evidence snapshot is persisted.

## Current migration limitation

Some schema evolution occurs at repository startup. This is accepted only for the local MVP. Versioned migrations and PostgreSQL are required before production data is introduced.

## Planned evidence metadata

A future immutable evidence snapshot should record:

```text
source connection
acquisition mode
source revision
acquisition policy
sanitization policy
content checksum
classification
credential reference
request trace
```

Secret values are never part of the snapshot.
