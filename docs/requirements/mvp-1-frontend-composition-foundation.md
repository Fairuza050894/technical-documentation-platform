# MVP 1 Frontend Composition and CSS Foundation

## Purpose

Reduce frontend maintainability risk without changing product behavior or intentionally
redesigning the interface.

## Functional requirements

1. `App.tsx` remains the application composition root and delegates application chrome and route
   rendering to explicit app-layer components.
2. Global navigation and page-context resolution are pure functions with unit tests.
3. Runtime health loading uses the shared API client.
4. Existing browser routes, workspace selection, project workbench navigation, System status,
   loading states, error states, and not-found behavior remain available.
5. `globals.css` becomes an explicit ordered import manifest.
6. Existing CSS rules are separated by foundation, application shell, shared components, and
   product-module responsibility.
7. Existing selector names and design tokens remain compatible.

## Non-functional requirements

- no backend API or database contract changes;
- no new runtime dependency;
- no intentional visual redesign;
- TypeScript strict mode and ESLint remain green;
- existing frontend component tests remain green;
- production build remains green;
- documentation indexes remain current;
- architecture fitness tests prevent regression to a monolithic application shell or CSS entry
  file.

## Acceptance criteria

- `frontend/src/app/App.tsx` is no more than 340 lines;
- application-shell markup is outside `App.tsx`;
- global navigation and page-context tests pass;
- `frontend/src/styles/globals.css` contains only the controlled import manifest;
- no style file contains patch-history comments;
- `make docs-check`, `make verify`, and `make audit-frontend` pass;
- visual review confirms no unintended change to desktop navigation, Workspace context, Project
  Workbench, Documents identity, or responsive navigation.
