# ADR-017: Compose the Frontend Shell and Split CSS by Responsibility

- Status: Accepted
- Date: 2026-08-04
- Decision owners: Product Engineering and Technical Documentation

## Context

The frontend has stable behavior and comprehensive component tests, but its composition has
become concentrated in `App.tsx` and one chronological `globals.css` file. `App.tsx` combines
browser routing, workspace resolution, runtime health, navigation, application chrome, route
rendering, and system-status content. `globals.css` contains 4,359 lines and patch-history
sections spanning application chrome and multiple product modules.

The current visual language is approved for continued MVP work. The change must improve
maintainability without intentionally changing routes, API contracts, DOM semantics, design
tokens, or visual behavior.

## Decision

1. Keep `App.tsx` as the stateful application composition root.
2. Extract application shell, sidebar, utility bar, route content, route states, system status,
   navigation metadata, and runtime types into explicit app-layer files.
3. Move backend-health loading into a dedicated hook that uses the shared API client.
4. Keep the existing deterministic browser-history router and canonical URLs.
5. Keep `globals.css` as a stable import manifest.
6. Split CSS into foundation, application-shell, shared-component, and module-responsibility
   files while preserving the original source order.
7. Do not introduce CSS Modules, CSS-in-JS, a new router, or a UI framework in this patch.
8. Add architecture fitness tests that bound `App.tsx`, enforce the CSS import manifest, and
   prohibit patch-history comments in style source.
9. Require existing component tests, linting, documentation freshness, and production build to
   remain green.

## Consequences

- Application chrome and route rendering can evolve independently.
- CSS ownership is visible without changing selector names or cascade order.
- Future module extraction has a stable place for module-specific styles.
- Existing large workspace components remain known follow-up work rather than being rewritten
  in one high-risk patch.
- Hard-coded color normalization, 44-pixel touch targets, dark mode, and broader responsive work
  remain separate visual decisions.
