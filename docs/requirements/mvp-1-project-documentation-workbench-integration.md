# MVP 1 — Project Documentation Workbench Integration

## Objective

Integrate the 0010A Project documentation checklist, 0010B evidence/claims, and 0010C deterministic
readiness into the existing Project Workbench without duplicating governance policy in the
frontend.

## Information architecture

The existing six Project stages remain unchanged: Overview, Features, Sources, API Catalog,
Changes, and Documents. Documentation governance is integrated into Overview rather than adding a
new route or duplicating DocumentsWorkspace.

The Overview answers, from canonical backend state:

- which Project document types are required or supplementary;
- whether a governed document version exists;
- whether minimum governed inputs are ready;
- which blockers or warnings remain;
- which remediation is required;
- which governed claims and evidence references support the document context;
- which existing technical stage is the next truthful navigation target when one exists.

## Canonical data

The frontend consumes these read contracts:

- `GET /api/projects/{project_id}/documentation-checklist`;
- `GET /api/projects/{project_id}/readiness`;
- `GET /api/projects/{project_id}/evidence`;
- `GET /api/projects/{project_id}/claims`.

The frontend may format, group, and map responses to user-facing labels. It must not reimplement
document requirement policy, claim classification rules, readiness rules, blocker logic, or
eligibility rules.

## Status separation

The UI keeps these concepts visibly distinct:

- requirement: Required / Supplementary;
- availability: Available / Not created;
- readiness: Ready / Ready with gaps / Blocked;
- lifecycle: Draft / In review / Changes requested / Approved / Previous version.

A missing document can therefore be ready, and an available document can still have readiness
gaps.

## Missing information and traceability

Each document row exposes backend findings in an expandable readiness detail area. Findings show
the backend message, remediation, severity, and rule code. The UI does not reinterpret whether a
finding blocks eligibility.

Relevant governed claims are displayed with user-facing Observed, Inferred, and Unverified labels.
Evidence directly referenced by those claims is summarized by evidence kind. Raw payloads,
credentials, local artifact paths, and secret values are never rendered.

## Navigation

Routing remains deterministic and truthful:

- missing technical source evidence can navigate to Sources;
- missing normalized Catalog snapshot evidence can navigate to API Catalog;
- document approval gaps can navigate to Documents;
- unsupported future evidence kinds such as user journeys, deployment/runtime evidence, or UAT
  results remain explicit gaps and do not receive a fake navigation target.

The existing Project next-action resolver may consume readiness findings only for these explicit
routing mappings.

## Archived Projects

Archived Projects keep documentation governance, readiness, evidence, claims, and existing
documents readable. The integration adds no mutation and preserves the existing read-only notice.

## UX and visual requirements

- use the established operational workbench language and `workbench.css` ownership;
- avoid a new dashboard/card wall;
- use a flat readiness list with compact summary metrics;
- use friendly labels instead of raw enum values as primary copy;
- preserve keyboard access through native buttons and details/summary disclosure;
- preserve mobile and narrow-screen behavior;
- do not introduce gradients, glass, glow, or AI-styled decoration.

## Non-goals

This slice does not implement enterprise document generation, template CRUD, new evidence
collectors, claim authoring UI, readiness-policy changes, impact/versioning rules, AI drafting,
Vibium/browser automation, GitHub/GitLab collectors, MCP, or unrelated route redesign.

## Acceptance criteria

- Overview renders canonical Project documentation and readiness from backend APIs;
- all ten document types can render without frontend policy hardcoding;
- requirement, availability, readiness, and lifecycle remain distinct;
- blocker/warning remediation is visible;
- claims and their directly referenced evidence are traceable without raw payload exposure;
- unsupported missing-input families are shown without false navigation;
- archived Project governance remains readable;
- existing six-stage URLs and Workspace context are unchanged;
- workbench CSS remains the canonical owner;
- focused frontend tests, architecture tests, full verification, and production build pass.
