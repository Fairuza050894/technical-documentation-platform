# ADR-021: Integrate Document Governance into the Existing Project Overview

- Status: Accepted
- Date: 2026-08-10
- Decision owners: Product Engineering and Technical Documentation

## Context

0010A established the enterprise Project document registry and checklist. 0010B established
immutable evidence and classified claims. 0010C established deterministic readiness and
missing-information findings. The Project Workbench still presents operational source/snapshot
heuristics and does not expose these governance contracts to users.

Adding another global dashboard or another Project stage would duplicate navigation and make the
existing Documents stage ambiguous. Reimplementing readiness in React would also create a second
source of truth.

## Decision

1. Integrate Project documentation governance into the existing Workbench Overview.
2. Keep the existing six Project stages and deep-link contract unchanged.
3. Consume the 0010A checklist, 0010B evidence/claims, and 0010C readiness through typed frontend
   read clients.
4. Keep requirement, availability, readiness, lifecycle, and eligibility as separate concepts.
5. Present all canonical document types as one compact readiness list rather than a card grid.
6. Present backend findings and remediation without recalculating blocker severity in the UI.
7. Present relevant claims and directly referenced evidence as traceability context.
8. Route only missing-input families that have a truthful implemented destination: Sources, API
   Catalog, or Documents. Unsupported evidence collectors remain visible gaps without fake actions.
9. Keep archived Project governance readable and introduce no mutation in this slice.
10. Keep `modules/workbench.css` as the sole owner of the new Workbench presentation.
11. Remove the existing Workbench next-action gradient so the integrated surface remains within the
    established flat operational visual language.
12. Keep enterprise document generation, claim authoring, evidence collection expansion, and AI
    drafting outside this decision.

## Consequences

- Users can understand document coverage, readiness, missing information, and traceability without
  switching between disconnected dashboards.
- Backend governance remains the source of truth.
- Existing browser routes, Workspace selection, Project context, and DocumentsWorkspace behavior
  remain stable.
- Future generators and collectors can extend capability without changing the Overview information
  architecture.
