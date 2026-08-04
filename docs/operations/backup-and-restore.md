# Backup and Restore

| Field | Value |
|---|---|
| Document ID | TDP-OPS-002 |
| Status | Controlled draft |
| Owner | Platform Operations and Data Owner |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Scope

This procedure covers the local MVP SQLite database and local artifact store. It is not a production disaster-recovery design.

## Backup set

```text
.runtime/tdp.sqlite3
.runtime/artifacts/
configuration references required to interpret the data
application commit and schema state
```

Never include secrets in the backup package.

## Local backup procedure

1. stop the backend to prevent concurrent writes;
2. confirm the SQLite file and artifact directory exist;
3. copy both into a dated, access-controlled location;
4. calculate checksums;
5. record the application commit and environment;
6. restart the backend and verify readiness.

## Restore procedure

1. preserve the current runtime directory before replacement;
2. restore into an isolated validation location first;
3. verify backup checksums;
4. start the application against the restored copy;
5. verify `/api/health/ready`;
6. inspect representative Workspace, Project, Source, and Document records;
7. authorize promotion of the restored copy;
8. record the restore result.

## Required production controls

- scheduled and monitored backups;
- encryption and access control;
- defined RPO and RTO;
- retention and deletion policy;
- geographically appropriate redundancy;
- regular restore tests;
- evidence of test results and corrective actions.

RPO and RTO are not defined by this repository and require organizational approval.
