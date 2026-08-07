# MVP 1 Frontend CSS Canonical Ownership

## Purpose

Reduce CSS cascade ambiguity without redesigning the product or changing established visual
behavior. Module-specific layout rules have one canonical module owner, while compatibility
migration remains incremental and visually verified.

## Ownership rules

1. `foundation.css` remains the reset, element baseline, and legacy-compatibility layer.
2. `application-shell.css` owns persistent application chrome.
3. `components.css` owns reusable controls and page primitives.
4. Module-specific selectors belong to their product workspace module.
5. A module must not define another module's selector solely to gain later cascade precedence.
6. Import order in `globals.css` remains an explicit compatibility contract.
7. Existing shared duplicates are not removed in bulk; each migration requires focused visual
   acceptance.
8. Project Workbench owns:
   - project stage navigation;
   - project readiness summary grid;
   - project documentation workflow map.
9. The stage navigation keeps all six implemented stage labels understandable at desktop width.
10. Broader responsive redesign, token redesign, CSS Modules, CSS-in-JS, and framework changes are
    out of scope.

## Acceptance criteria

- Workbench-specific navigation/readiness selectors no longer exist in `features.css`.
- Their effective desktop and responsive layout is preserved in `workbench.css`.
- `API Catalog` and `Documents` stage labels are no longer clipped at the normal desktop layout.
- `features.css` contains only Feature/Module workspace responsibility plus shared primitives it
  consumes.
- Architecture tests prevent the Workbench selectors from drifting back into `features.css`.
- All repository quality gates, documentation checks, and the production frontend build pass.
