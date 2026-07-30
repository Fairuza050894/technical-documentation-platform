# MVP 1 — Visual Refinement R1

## Objective

Correct the first visual-refinement candidate before introducing a project-centric workbench.

## Scope

- stabilize asynchronous frontend tests under normal parallel test load;
- normalize neutral, accent, and semantic color tokens;
- improve inactive sidebar contrast and reduce group-label letter spacing;
- compress the operational signal strip and remove decorative icon circles;
- present Attention and Quick actions as one continuous operational rail;
- flatten the Documents workspace to remove nested-card hierarchy;
- prevent topbar badges from clipping or overlapping;
- preserve deterministic source evidence, document lifecycle behavior, and existing API contracts.

## Out of scope

- project-context routing;
- Documentation Blueprint;
- Template Library;
- repository ingestion;
- release package generation.

## Acceptance criteria

1. `git diff --check` passes.
2. All backend and frontend quality gates pass.
3. The sidebar remains readable without adding decorative colors.
4. Operational metrics read as a compact signal strip rather than four cards.
5. The operational rail uses one outer boundary with internal dividers.
6. Documents generation, history, detail, and comparison use a flatter page hierarchy.
7. No workflow state, API request, or document lifecycle behavior changes.
