# ADR-006: Deterministic snapshot comparison

## Status

Accepted.

## Decision

Change detection compares normalized catalog snapshots, not raw OpenAPI text. Operation identity is HTTP method plus path; schema identity is component name. Every result preserves before and after JSON Pointer evidence.

The comparator is deterministic and does not use AI. Removed operations, removed schemas, removed properties, newly required fields, removed responses, and newly required parameters are classified as breaking.

## Consequences

Formatting-only source changes do not create catalog changes. The first version computes comparisons on demand and does not persist comparison reports.
