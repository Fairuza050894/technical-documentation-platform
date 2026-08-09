# MVP 1 Application Shell and Operational Overview CSS Ownership

## Purpose

Complete the frontend ownership migration by removing the remaining application-shell and
Operational Overview compatibility rules from unrelated style layers.

This is the final broad CSS ownership migration before the B4 cross-route acceptance sweep.

## Canonical ownership

`application-shell.css` owns:

- application frame and main content;
- persistent sidebar and product mark;
- workspace context baseline;
- primary navigation groups/items/icons;
- sidebar service state;
- utility bar and runtime context;
- workspace canvas;
- shell responsive behavior at the existing 980px, 900px, 760px, and 640px breakpoints.

`modules/overview.css` owns:

- operational signal region;
- activity and project-health composition;
- operational rail;
- Operational Overview headings;
- live-data provenance;
- Overview page actions;
- Overview-only responsive composition.

`components.css` continues to own reusable page, form, table, button, feedback, and System Status
primitives.

`foundation.css` owns global element/accessibility behavior, including focus treatment, reduced
motion, document scroll padding, and base elements.

## Compatibility

The migration preserves the currently effective cascade rather than restoring obsolete legacy
values. In particular:

- the desktop sidebar retains its current dark operational treatment;
- 980px keeps the current 210px shell column;
- 760px keeps the existing stacked shell and horizontally scrollable navigation;
- utility runtime metadata remains hidden at the existing narrow breakpoint;
- main-content and workspace-canvas spacing remain unchanged;
- System Status and form grids still collapse to one column at 760px;
- Overview page actions keep their existing desktop and narrow alignment;
- no routes, navigation events, workspace selection, data loading, or product behavior change.

## Valid contextual overrides

Contextual descendants in Workbench, Workspaces, Features, Sources, Catalog, Changes, and Documents
remain valid when they alter a shared primitive only inside their own module. For example,
`workspace-context__chevron` may still have Workspace Switcher state rules and shared buttons/tables
may still have module-scoped layout overrides.

## Non-goals

No visual redesign, token redesign, typography redesign, dark mode, new mobile navigation, API
change, domain change, or persistence change is introduced.

## Acceptance criteria

- foundation and Overview no longer own application-shell selectors;
- Application Shell contains the current desktop and responsive shell contract;
- Overview-only primitives are absent from shared components;
- shared form/System Status responsive rules are absent from Overview;
- global focus/reduced-motion/scroll behavior is foundational;
- duplicate CSS selector-name count decreases from 35 to 11 or lower;
- focused App/Shell/Overview/Workbench tests pass;
- full repository verification, production build, documentation generation, and whitespace pass.
