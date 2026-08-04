# User Flows

| Field | Value |
|---|---|
| Document ID | TDP-PROD-004 |
| Status | Controlled draft |
| Owner | Product Management and User Experience |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Current source-to-document flow

```mermaid
flowchart LR
W[Select Workspace] --> P[Open Project]
P --> F[Register Feature or Module]
F --> S[Import OpenAPI Source]
S --> Y[Synchronize Catalog Snapshot]
Y --> C{Baseline available?}
C -- Yes --> D[Compare Snapshots]
C -- No --> G[Generate Technical Source Overview]
D --> G
G --> V[Create or reuse immutable version]
V --> R[Submit for review]
R --> Q{Review decision}
Q -- Request changes --> S
Q -- Approve --> A[Approved version]
A --> N[Newer approved version supersedes prior version]
```

## Current navigation flow

```mermaid
flowchart TD
H[Workspace Home] --> PR[Project Registry]
PR --> O[Project Overview]
O --> FT[Features]
O --> SO[Sources]
SO --> AC[API Catalog]
AC --> CH[Changes]
CH --> DO[Documents]
DO --> RV[Review - planned stage]
RV --> RL[Release - planned stage]
```

## Future governed version flow

```mermaid
flowchart LR
RR[Requirement Revision] --> ES[Evidence Snapshot]
ES --> CS[Canonical Change Set]
CS --> IA[Impact Analysis]
IA --> VP[Version Policy]
VP --> DV[Document Version Decision]
DV --> DG[Document Generation]
DG --> HR[Human Review]
HR --> RE[Release Eligibility]
```

## Flow rules

- Workspace context remains active while a Project is open.
- Project and Feature identity must not be inferred from a free-text document.
- A generated version records evidence and policy references.
- Approval is a governed mutation and must never accept a client-supplied actor.
- Planned steps must remain visibly marked as planned until implemented.
