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
