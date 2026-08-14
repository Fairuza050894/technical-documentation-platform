# MVP 1 — Project Documentation Registry Visual Polish

## Objective

Present governed Project documentation readiness as a stable enterprise registry that is easy to
scan across document types without changing readiness, availability, or workflow policy.

## Desktop contract

The registry uses four aligned visual zones:

1. Document identity — document name, requirement marker, and automation profile.
2. Status — availability, readiness, and current lifecycle status.
3. Readiness — blocker/warning summary and evidence/claim metrics.
4. Next step — one right-aligned primary navigation action when an action exists.

A lightweight column heading establishes the alignment contract. Every document row uses the same
grid tracks and aligns content from the top so one-line badges and actions do not drift vertically
against two-line identity or readiness content.

`Readiness details` remains an accessible native disclosure below the primary row. The disclosure
does not change readiness semantics or navigation behavior.

## Responsive contract

At medium widths the registry becomes a two-column semantic layout:

- identity + status;
- readiness + action;
- details across the row.

At mobile widths the row stacks in this order:

- identity;
- status;
- readiness;
- action;
- details.

The desktop-only visual column heading is hidden once the two-column layout is active. No horizontal
scroll is introduced by the documentation registry.

## Boundaries

- no backend/readiness policy changes;
- no business-copy rewrite;
- no sidebar, utility bar, stage navigation, or dashboard redesign;
- shared button and status primitives remain owned by `components.css`;
- documentation registry layout remains owned by `modules/workbench.css`;
- no gradients, glass effects, glow, decorative illustrations, or AI-style visual treatments.

## Operator-facing readiness language

The backend readiness policy is the canonical owner of both deterministic rule semantics and the
plain-language `message` and `remediation` returned for each finding. The frontend renders those
fields directly and does not map or duplicate readiness `rule_code` values.

Rule identity, severity, `missing_input`, evidence requirements, and deterministic eligibility remain
unchanged. Internal machine identifiers remain available through API, diagnostics, and audit paths,
while the normal operator view explains what information is missing and what the user should do next.
