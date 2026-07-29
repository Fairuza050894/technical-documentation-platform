# MVP 1 Requirement: Product UI Foundation and Operational Overview

## Objective

Provide a professional, source-backed technical workspace that supports fast operational
decisions and consistent navigation across the MVP source-to-document workflow.

## Functional requirements

1. Overview is the default workspace.
2. Navigation is grouped into Workspace, Sources, Documentation, and System.
3. Unimplemented placeholder modules are not shown in primary navigation.
4. The global utility bar shows workspace, environment, and backend availability.
5. Overview loads real data from project, source, synchronization, and document APIs.
6. Overview displays active projects, ready sources, completed snapshots, and pending reviews.
7. Attention Required displays failed synchronizations, unsynchronized sources, pending document
   actions, and breaking findings when present.
8. Recent Activity combines synchronization and document lifecycle timestamps.
9. Project Health summarizes source count, normalized operation count, latest synchronization,
   and approved or pending document state.
10. Quick actions navigate to existing MVP workspaces.
11. System status displays health endpoint metadata and deterministic documentation policies.

## UX requirements

- No gradient, glassmorphism, decorative illustration, or fabricated metric.
- Dense tables use semantic captions and visible row hierarchy.
- Status colors have text labels and never rely on color alone.
- Keyboard focus is clearly visible.
- Reduced-motion preferences are respected.
- Navigation and dashboard remain usable on narrow screens.
- Existing Projects, Sources, API Catalog, Changes, and Documents functionality remains intact.

## Acceptance criteria

- Overview renders source-backed zero states when the repository has no runtime data.
- Overview renders real counts and attention items from API fixtures.
- Quick actions open the corresponding existing workspace.
- System status reports backend version and environment.
- Sync History is absent until a dedicated implemented workspace exists.
- Frontend lint, tests, and production build pass.
- Existing backend quality gates remain green.
