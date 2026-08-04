# Ownership and Approval

| Field | Value |
|---|---|
| Document ID | TDP-GOV-003 |
| Status | Controlled draft |
| Owner | Product Governance |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Responsibility model

| Role | Accountability |
|---|---|
| Product Owner | Product scope, priority, and release intent |
| Architecture Owner | Architecture coherence and ADR acceptance |
| Technical Documentation Owner | Documentation structure, accuracy, and control |
| Engineering Owner | Implementation and technical verification |
| Security Owner | Security controls, risk acceptance, and exceptions |
| Quality Owner | Test strategy and release evidence |
| Release Authority | Final production release authorization |

One person may temporarily perform multiple roles during local development, but the roles remain distinct for future separation of duties.

## Approval boundaries

The following may be accepted as project decisions by repository maintainers:

- ADRs;
- coding standards;
- quality gates;
- local-development procedures;
- roadmap sequencing.

The following require an authorized organizational decision outside repository automation:

- legal ownership and license;
- production security acceptance;
- compliance approval;
- risk acceptance;
- production release;
- data-retention obligations;
- customer or regulatory commitments.

## Approval evidence

A formal approval record should include:

```text
document or release identifier
version or commit
decision
approver identity
approver role
scope
conditions
timestamp
evidence reference
```

The local identity provider is not sufficient for production approval.
