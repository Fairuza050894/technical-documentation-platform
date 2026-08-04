# Data Classification and Retention

| Field | Value |
|---|---|
| Document ID | TDP-SEC-001 |
| Status | Controlled draft |
| Owner | Security and Data Governance |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Classification model

| Class | Examples | Repository rule |
|---|---|---|
| Public | approved public README or release material | only after authorization |
| Internal | architecture, PRD, test strategy | permitted in controlled repository |
| Confidential | customer source specifications, generated project documents | do not commit unless explicitly approved |
| Restricted | passwords, tokens, private keys, personal data, secret values | never commit; never embed in generated documentation |

Repository project documentation defaults to **Internal**.

## Current data locations

| Data | Location | Default class |
|---|---|---|
| Source code and controlled repository docs | Git repository | Internal |
| Local database | `.runtime/tdp.sqlite3` | Confidential |
| Imported source artifacts | `.runtime/artifacts` | Confidential |
| Generated project documents | local runtime store | Confidential |
| Credentials and tokens | environment or future secret manager | Restricted |

## Retention principles

- retention periods require organizational, contractual, and legal approval;
- immutable audit evidence must not be deleted ad hoc;
- secrets must not be retained in documentation;
- obsolete controlled documents are superseded or retired, not silently overwritten;
- local development data should be removed when no longer required;
- production retention and disposal must be enforced by policy and verified.

## Future remote evidence

Before persistence, connector responses must be classified, prohibited fields must be redacted, and the sanitized snapshot must be checksummed. Credential values are never part of the snapshot.
