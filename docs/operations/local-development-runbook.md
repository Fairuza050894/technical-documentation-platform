# Local Development Runbook

| Field | Value |
|---|---|
| Document ID | TDP-OPS-001 |
| Status | Controlled draft |
| Owner | Engineering and Platform Operations |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Start

```bash
make bootstrap
make dev-backend
make dev-frontend
```

Backend: `http://127.0.0.1:8000`  
Frontend: `http://127.0.0.1:4173`

## Verify

```bash
make docs-check
make verify
```

## Health

```bash
curl -s http://127.0.0.1:8000/api/health/live
curl -s http://127.0.0.1:8000/api/health/ready
curl -s http://127.0.0.1:8000/api/identity/me
```

## Common checks

```bash
git status --short --branch
git diff --check
lsof -nP -iTCP:8000 -sTCP:LISTEN
lsof -nP -iTCP:4173 -sTCP:LISTEN
```

## Runtime boundaries

- `.runtime` contains local data and is not source code;
- real `.env` files are local and are not committed;
- the local identity provider is development-only;
- do not use real customer secrets or production evidence in local fixtures.

## Stop

Stop foreground processes with `Control+C`. Confirm ports are no longer listening before restarting with different configuration.
