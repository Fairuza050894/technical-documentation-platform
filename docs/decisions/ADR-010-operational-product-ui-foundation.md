# ADR-010: Operational Product UI Foundation

- Status: Accepted
- Date: 2026-07-29

## Context

The engineering foundation exposed every MVP capability, but the application shell still
resembled a starter dashboard. The Overview page described frontend and backend readiness
instead of helping technical writers and reviewers understand operational work.

The product requires a professional, information-dense interface without decorative metrics,
AI-generated filler, or assumptions that are not backed by the platform data model.

## Decision

The MVP uses a compact operational shell with:

- grouped navigation based on user workflow;
- a persistent workspace and runtime context bar;
- a source-backed Overview assembled from existing APIs;
- semantic status colors for success, warning, danger, and neutral conditions;
- dense tables and compact form controls for technical users;
- visible keyboard focus, semantic landmarks, table captions, and reduced-motion support;
- responsive navigation without introducing a second mobile application structure.

The Overview loads projects, sources, synchronization runs, and document versions through the
existing application APIs. It computes display-only aggregates in the frontend. No metrics are
invented or persisted by the UI.

The application does not imitate Grafana branding or visual assets. It adopts comparable
principles: information density, operational hierarchy, explicit status, and efficient
drill-down.

## Consequences

- The first page now supports operational decisions instead of reporting implementation status.
- Engineering constraints move to System status.
- Existing backend contracts remain unchanged.
- The frontend performs several read requests for the Overview; a dedicated aggregation endpoint
  may be introduced after MVP usage demonstrates that it is necessary.
- All workspaces share the same design tokens and compact component treatment.
