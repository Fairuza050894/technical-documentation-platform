
# Security Policy

## Current support status

The Technical Documentation Platform is an MVP under active development. It is
not approved for public internet exposure or enterprise production use.

The current `local` identity provider exists only for development and automated
tests. Application startup rejects this mode when `TDP_ENVIRONMENT` is
`staging` or `production`.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability.

Report the issue privately to the repository owner or the security contact
defined by the organization operating this repository. Include:

- affected commit or release;
- affected endpoint or component;
- reproduction steps;
- expected and observed impact;
- relevant logs with secrets removed.

Do not include credentials, tokens, private source files, generated documents,
or personal data in the report.

## Response expectations

The repository owner should acknowledge a report, assess severity, document the
decision, and provide a remediation or risk-acceptance plan before disclosure.

## Security boundaries

Until a production identity adapter and authorization policy are implemented:

- keep the service bound to trusted development networks;
- do not treat local-development workflow approvals as legal non-repudiation;
- do not store production secrets in `.env` files;
- keep `.runtime`, imported artifacts, databases, and generated documents out
  of Git;
- run `make verify` before every commit and require the GitHub `Verify` check
  before merging.
