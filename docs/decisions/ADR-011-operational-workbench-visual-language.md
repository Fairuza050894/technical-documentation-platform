# ADR-011: Operational Workbench Visual Language

- Status: Accepted
- Date: 2026-07-29
- Decision owners: Product Engineering and Technical Documentation

## Context

The Product UI Foundation introduced grouped navigation and a source-backed Overview, but the
result still relied on a repeated card-grid composition that resembled generic generated
dashboard templates. Navigation also lacked durable iconography, and native controls were not
visually aligned across workspaces.

The platform is intended for technical authors, reviewers, and engineering stakeholders. The UI
must support scanning, comparison, review, and operational follow-up without decorative or
fabricated content.

## Decision

Adopt an operational workbench visual language with the following rules:

1. Primary navigation uses one consistent inline SVG icon system with no runtime icon dependency.
2. The Overview uses a flat signal strip, activity stream, project health matrix, and right-hand
   action rail instead of a grid of independent metric cards.
3. Tables remain the primary structure for dense technical facts.
4. Native selects, inputs, and textareas remain semantic and mobile-friendly, with a shared
   control height, label hierarchy, focus state, and compact spacing.
5. Panels use restrained borders and minimal shadow. Rounded card repetition is not used as the
   default page composition.
6. Status color is semantic and supplementary; text labels remain mandatory.
7. No gradient, glassmorphism, decorative illustration, or invented chart is introduced.
8. Reduced-motion and keyboard-visible focus behavior remain part of the foundation.

## Design references

The implementation follows established enterprise design-system principles:

- persistent application navigation and breadcrumbs;
- structured, readable data presentation;
- compact lists and tables for technical objects;
- native select controls where appropriate;
- consistent design tokens and reusable interaction patterns.

The platform does not copy another product's visual identity.

## Consequences

- Overview structure is more operational and less template-like.
- Sidebar navigation gains stronger scanability.
- Existing workspaces receive consistent controls and denser tables through shared CSS.
- The icon set is maintained as local source code and adds no package dependency.
- Future workspaces must use the same tokens and interaction patterns.

## Validation

The dedicated visual-refinement audit checks icon mapping, workbench composition, absence of the
old metric-card Overview pattern, control styling, typography tokens, accessibility selectors,
frontend tests, and production build.
