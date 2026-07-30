# MVP 1 Requirement: Visual Refinement and Product Polish

## Objective

Provide a professional technical-platform interface that supports fast operational scanning and
does not resemble a generic generated dashboard template.

## Functional requirements

1. Every primary sidebar item displays a consistent semantic icon.
2. The active navigation item remains distinguishable by text, icon, background, and position
   indicator.
3. Overview displays source-backed workspace metrics without fabricated values.
4. Overview presents recent synchronization and document activity as an event stream.
5. Overview presents active project state in a compact health table.
6. Overview presents blocking or review conditions in an attention rail.
7. Quick actions navigate to Projects, Sources, API Catalog, and Documents.
8. Runtime scope, environment, and backend availability remain visible in application chrome.
9. Existing workspace behavior and API contracts remain unchanged.

## Visual requirements

1. Use a compact enterprise workbench composition.
2. Do not use a repeated grid of rounded metric cards as the primary Overview structure.
3. Use restrained borders, minimal shadow, and limited radius.
4. Align labels, controls, helper text, and action placement consistently.
5. Use a shared native-select appearance and control height.
6. Use tabular numerals for operational counts and technical metadata where appropriate.
7. Preserve dense, readable tables.
8. Do not use gradient, glassmorphism, decorative illustration, or fake charts.

## Accessibility requirements

1. Navigation icons are decorative and hidden from assistive technology.
2. Navigation buttons retain accessible names from visible labels.
3. Focus indicators are visible for keyboard users.
4. Status is communicated with text, not color alone.
5. Tables keep captions or equivalent accessible names.
6. Reduced-motion preferences are respected.
7. Responsive navigation remains usable at narrow widths.

## Acceptance criteria

- Sidebar contains icons for Overview, Projects, Source Registry, API Catalog, Change Analysis,
  Documents, and System Status.
- Operational Overview contains Workspace metrics, Recent activity, Project health, Attention
  required, and Quick actions.
- `OperationalOverview.tsx` does not use the legacy `metric-card` component.
- Project health remains available as an accessible table.
- Existing backend tests, frontend tests, linting, and production build pass.
- `make audit-visual-refinement` produces one complete report in `~/Downloads`.
- Visual review is completed before commit and push.
