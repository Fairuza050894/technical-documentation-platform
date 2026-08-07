# Frontend Style Layers

The frontend keeps one stable entry point, `globals.css`, that imports style layers in an explicit
cascade order. The layers do not use CSS `@layer` yet because introducing cascade layers would
change precedence for existing selectors.

```text
tokens.css
globals.css
├── foundation.css
├── application-shell.css
├── components.css
└── modules/
    ├── overview.css
    ├── workbench.css
    ├── workspaces.css
    ├── features.css
    ├── changes.css
    └── documents.css
```

Rules:

- `foundation.css` contains reset, base element, and legacy-compatible foundation rules.
- `application-shell.css` owns the persistent sidebar, utility bar, and application frame.
- `components.css` owns reusable controls, forms, notices, tables, and page primitives.
- module files own selectors that are specific to one product workspace.
- import order in `globals.css` is a controlled compatibility contract.
- new patch-history comments are prohibited; comments describe responsibility, not chronology.
- new selectors should use existing tokens before adding hard-coded values.
- moving a selector between layers requires visual review because source order is meaningful.

## Canonical ownership

Ownership is based on responsibility, not on the route that happens to import later in the cascade.

| Selector family | Canonical owner |
| --- | --- |
| application shell, sidebar, utility bar | `application-shell.css` |
| reusable buttons, forms, notices, tables, page primitives | `components.css` |
| operational overview workspace | `modules/overview.css` |
| project workbench stage navigation, readiness summary, workflow map | `modules/workbench.css` |
| workspace registry and switcher | `modules/workspaces.css` |
| feature/module registry and documentation map | `modules/features.css` |
| deterministic changes result workspace | `modules/changes.css` |
| document-specific identity/workflow additions | `modules/documents.css` |

A module-specific selector must not be declared in another module merely to gain later cascade
precedence. When an existing compatibility override is migrated, first copy its effective
declarations to the canonical owner, preserve responsive behavior, then remove the later override.
Shared legacy declarations in `foundation.css` are migrated separately in small, visually verified
slices.
