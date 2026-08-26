#!/usr/bin/env bash
set -euo pipefail

if [ ! -f "backend/src/tdp/main.py" ]; then
  echo "ERROR: Jalankan dari root repository."
  exit 1
fi

echo "============================================"
echo " Phase 1 Foundation Patch"
echo " WS 1.3 + 1.4 + 3.1 + 3.2"
echo "============================================"
echo ""

echo "[1/6] Creating audit module..."
mkdir -p backend/src/tdp/audit

cat > backend/src/tdp/audit/__init__.py << 'EOF'
"""Audit trail bounded context."""
EOF

cat > backend/src/tdp/audit/model.py << 'EOF'
"""Audit event domain model.

Reference: ISO/IEC 27001:2022 A.8.15 (Logging)
Every mutation on the system produces an immutable AuditEvent
that can be queried for compliance and incident investigation.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class AuditAction(StrEnum):
    """Classifies the operation that was performed."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    REVIEW = "review"
    APPROVE = "approve"
    REJECT = "reject"
    PUBLISH = "publish"
    ARCHIVE = "archive"
    EXPORT = "export"
    IMPORT = "import"
    LOGIN = "login"
    LOGOUT = "logout"


@dataclass(frozen=True)
class AuditEvent:
    """Immutable record of a single auditable action.

    Frozen dataclass guarantees that once written the event cannot
    be mutated — critical for forensic integrity.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    actor_id: str = ""
    actor_display_name: str = ""
    action: AuditAction = AuditAction.READ
    resource_type: str = ""
    resource_id: str = ""
    workspace_id: str = ""
    project_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    request_id: str = ""
    ip_address: str = ""
    success: bool = True
    error_message: str = ""
EOF

cat > backend/src/tdp/audit/logger.py << 'EOF'
"""Structured audit logger.

Writes audit events as structured log entries via structlog.
In production these entries should be shipped to a SIEM or
append-only audit store.
"""
from __future__ import annotations

import structlog

from tdp.audit.model import AuditEvent

logger = structlog.stdlib.get_logger("audit")


class StructuredAuditLogger:
    """Thin facade that serialises AuditEvent into structlog."""

    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    def record(self, event: AuditEvent) -> None:
        """Persist a single audit event."""
        if not self._enabled:
            return

        logger.info(
            "audit_event",
            event_id=event.event_id,
            timestamp=event.timestamp.isoformat(),
            actor_id=event.actor_id,
            actor_display_name=event.actor_display_name,
            action=event.action.value,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            workspace_id=event.workspace_id,
            project_id=event.project_id,
            request_id=event.request_id,
            ip_address=event.ip_address,
            success=event.success,
            error_message=event.error_message,
            **event.metadata,
        )
EOF

cat > backend/src/tdp/audit/middleware.py << 'EOF'
"""ASGI audit middleware for FastAPI.

Intercepts every write request (POST/PUT/PATCH/DELETE) and
produces an AuditEvent *after* the response has been generated
so that the status code is captured.
"""
from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from tdp.audit.logger import StructuredAuditLogger
from tdp.audit.model import AuditAction, AuditEvent

_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

_METHOD_ACTION_MAP: dict[str, AuditAction] = {
    "POST": AuditAction.CREATE,
    "PUT": AuditAction.UPDATE,
    "PATCH": AuditAction.UPDATE,
    "DELETE": AuditAction.DELETE,
}


class AuditMiddleware(BaseHTTPMiddleware):
    """Records an audit event for every state-changing request."""

    def __init__(self, app, audit_logger: StructuredAuditLogger) -> None:  # noqa: ANN001
        super().__init__(app)
        self._audit = audit_logger

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.method not in _WRITE_METHODS:
            return await call_next(request)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        principal = getattr(request.state, "principal", None)

        event = AuditEvent(
            actor_id=getattr(principal, "subject_id", "anonymous") if principal else "anonymous",
            actor_display_name=(
                getattr(principal, "display_name", "") if principal else ""
            ),
            action=_METHOD_ACTION_MAP.get(request.method, AuditAction.UPDATE),
            resource_type=request.url.path,
            request_id=getattr(request.state, "request_id", ""),
            ip_address=request.client.host if request.client else "",
            success=200 <= response.status_code < 400,
            metadata={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        self._audit.record(event)
        return response
EOF

echo "[2/6] Creating rate limiting middleware..."
mkdir -p backend/src/tdp/presentation/http/middleware

cat > backend/src/tdp/presentation/http/middleware/rate_limiting.py << 'EOF'
"""In-memory sliding-window rate limiter.

Suitable for single-process deployments.  For multi-worker or
multi-node setups, replace the in-memory dict with Redis.

Reference: OWASP ASVS 4.0 — V11.1 Business Logic Security
"""
from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class SlidingWindowRateLimiter:
    """Thread-safe sliding window counter keyed by client IP."""

    def __init__(self, requests_per_minute: int) -> None:
        self._window_seconds: int = 60
        self._max_requests: int = requests_per_minute
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._lock: Lock = Lock()

    @property
    def max_requests(self) -> int:
        return self._max_requests

    def is_allowed(self, key: str) -> tuple[bool, int, int]:
        """Return (allowed, remaining, reset_epoch)."""
        now = time.time()
        window_start = now - self._window_seconds

        with self._lock:
            timestamps = self._windows[key]
            self._windows[key] = [t for t in timestamps if t > window_start]

            current = len(self._windows[key])
            if current >= self._max_requests:
                oldest = self._windows[key][0]
                reset_epoch = int(oldest + self._window_seconds)
                return False, 0, reset_epoch

            self._windows[key].append(now)
            remaining = self._max_requests - current - 1
            reset_epoch = int(now + self._window_seconds)
            return True, remaining, reset_epoch


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rejects requests that exceed the per-IP rate limit."""

    def __init__(self, app, requests_per_minute: int = 60) -> None:  # noqa: ANN001
        super().__init__(app)
        self._limiter = SlidingWindowRateLimiter(requests_per_minute)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        allowed, remaining, reset_epoch = self._limiter.is_allowed(client_ip)

        if not allowed:
            retry_after = max(reset_epoch - int(time.time()), 1)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": retry_after,
                },
                headers={
                    "X-RateLimit-Limit": str(self._limiter.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_epoch),
                    "Retry-After": str(retry_after),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self._limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_epoch)
        return response
EOF

echo "[3/6] Creating Docker files..."

cat > Dockerfile.backend << 'ENDOFDOCKER'
FROM python:3.12-slim AS builder
RUN pip install --no-cache-dir uv
WORKDIR /build
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --no-dev --frozen
COPY backend/src/ src/

FROM python:3.12-slim AS runtime
RUN groupadd --gid 1000 tdp && useradd --uid 1000 --gid tdp --create-home --shell /bin/bash tdp
WORKDIR /app
COPY --from=builder /build/.venv /app/.venv
COPY --from=builder /build/src /app/src
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    TDP_ENVIRONMENT=production \
    TDP_DATABASE_PATH=/data/tdp.sqlite3 \
    TDP_ARTIFACT_ROOT_PATH=/data/artifacts
RUN mkdir -p /data && chown tdp:tdp /data
USER tdp
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"]
CMD ["uvicorn", "tdp.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
ENDOFDOCKER

cat > Dockerfile.frontend << 'ENDOFDOCKER'
FROM node:22-slim AS builder
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts
COPY frontend/ .
RUN npm run build

FROM nginx:1.27-alpine AS runtime
RUN addgroup -g 1000 tdp && adduser -u 1000 -G tdp -s /bin/sh -D tdp
COPY --from=builder /build/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN chown -R tdp:tdp /usr/share/nginx/html && \
    chown -R tdp:tdp /var/cache/nginx && \
    chown -R tdp:tdp /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown tdp:tdp /var/run/nginx.pid
USER tdp
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1:80/health || exit 1
ENDOFDOCKER

cat > nginx.conf << 'EOF'
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "0" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

    location /api/ {
        proxy_pass         http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_set_header   X-Request-ID      $request_id;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    location = /health {
        access_log off;
        return 200 'ok';
        add_header Content-Type text/plain;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf)$ {
        expires    1y;
        add_header Cache-Control "public, immutable";
    }

    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

cat > docker-compose.yml << 'EOF'
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      TDP_ENVIRONMENT: production
      TDP_DATABASE_PATH: /data/tdp.sqlite3
      TDP_ARTIFACT_ROOT_PATH: /data/artifacts
      TDP_ALLOWED_ORIGINS: "http://localhost"
    volumes:
      - tdp-data:/data
    expose:
      - "8000"
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped

volumes:
  tdp-data:
EOF

cat > docker-compose.dev.yml << 'EOF'
services:
  backend:
    build:
      target: runtime
    command:
      - uvicorn
      - tdp.main:app
      - --reload
      - --host
      - "0.0.0.0"
      - --port
      - "8000"
    environment:
      TDP_ENVIRONMENT: development
      TDP_AUTH_MODE: local
    volumes:
      - ./backend/src:/app/src
      - ./.runtime:/data
    ports:
      - "8000:8000"

  frontend:
    ports:
      - "4173:80"
EOF

cat > .dockerignore << 'EOF'
.git
.github
.vscode
.venv
.mypy_cache
.pytest_cache
.ruff_cache
__pycache__
node_modules
dist
.runtime
*.sqlite3
*.pyc
*.pyo
.env
.env.*
docs
scripts
fixtures
CHANGELOG.md
CONTRIBUTING.md
README.md
SECURITY.md
EOF

echo "[4/6] Updating config.py..."

python3 << 'PYEOF'
from pathlib import Path

path = Path("backend/src/tdp/config.py")
content = path.read_text()

OLD = '    local_identity_email: str = "technical.writer@local.invalid"\n'
NEW = '''    local_identity_email: str = "technical.writer@local.invalid"

    # --- Phase 1: Security & Infrastructure ---
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    audit_enabled: bool = True

    # --- Future: Database & Authentication (Phase 1 continued) ---
    database_url: str = ""
    oidc_issuer: str = ""
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
'''

if OLD not in content:
    raise SystemExit("ERROR: config.py does not match expected content. Aborting.")

path.write_text(content.replace(OLD, NEW))
print("  config.py updated")
PYEOF

echo "[5/6] Updating main.py..."

python3 << 'PYEOF'
from pathlib import Path

path = Path("backend/src/tdp/main.py")
content = path.read_text()

OLD_IMPORT = "from tdp.presentation.http.middleware.request_id import RequestIdMiddleware"
NEW_IMPORT = """from tdp.audit.logger import StructuredAuditLogger
from tdp.audit.middleware import AuditMiddleware
from tdp.presentation.http.middleware.rate_limiting import RateLimitMiddleware
from tdp.presentation.http.middleware.request_id import RequestIdMiddleware"""

if OLD_IMPORT not in content:
    raise SystemExit("ERROR: main.py import block not found. Aborting.")
content = content.replace(OLD_IMPORT, NEW_IMPORT)

OLD_MIDDLEWARE = '''    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(RequestIdMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(runtime_settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )'''

NEW_MIDDLEWARE = '''    audit_logger = StructuredAuditLogger(enabled=runtime_settings.audit_enabled)
    application.state.audit_logger = audit_logger

    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(AuditMiddleware, audit_logger=audit_logger)
    if runtime_settings.rate_limit_enabled:
        application.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=runtime_settings.rate_limit_requests_per_minute,
        )
    application.add_middleware(RequestIdMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(runtime_settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )'''

if OLD_MIDDLEWARE not in content:
    raise SystemExit("ERROR: main.py middleware block not found. Aborting.")
content = content.replace(OLD_MIDDLEWARE, NEW_MIDDLEWARE)

path.write_text(content)
print("  main.py updated")
PYEOF

echo "[6/6] Updating Makefile and CI..."

python3 << 'PYEOF'
from pathlib import Path

mkpath = Path("Makefile")
mk = mkpath.read_text()

DOCKER_TARGETS = """
docker:
\tdocker compose build
\tdocker compose up -d

docker-dev:
\tdocker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

docker-stop:
\tdocker compose down

docker-logs:
\tdocker compose logs -f --tail=50
"""

if "docker:" not in mk:
    mk = mk.rstrip() + "\n" + DOCKER_TARGETS
    mkpath.write_text(mk)
    print("  Makefile updated")
else:
    print("  Makefile docker targets already present")

cipath = Path(".github/workflows/verify.yml")
ci = cipath.read_text()

OLD_CI = """      - name: Install backend dependencies
        run: uv sync --project backend --dev"""

NEW_CI = """      - name: Install backend dependencies
        run: uv sync --project backend --dev

      - name: Audit Python dependencies
        run: uv run --project backend pip audit --strict --desc
        continue-on-error: true

      - name: Audit Node dependencies
        run: npm audit --audit-level=moderate --prefix frontend
        continue-on-error: true"""

if "pip audit" not in ci:
    ci = ci.replace(OLD_CI, NEW_CI)
    cipath.write_text(ci)
    print("  verify.yml updated")
else:
    print("  verify.yml audit steps already present")
PYEOF

echo "[bonus] Creating test files..."

cat > backend/tests/test_audit.py << 'EOF'
"""Tests for audit trail module."""
from __future__ import annotations

import pytest

from tdp.audit.model import AuditAction, AuditEvent


class TestAuditAction:
    def test_action_values(self) -> None:
        assert AuditAction.CREATE == "create"
        assert AuditAction.APPROVE == "approve"
        assert AuditAction.LOGIN == "login"

    def test_action_is_str(self) -> None:
        assert isinstance(AuditAction.CREATE, str)


class TestAuditEvent:
    def test_defaults(self) -> None:
        event = AuditEvent()
        assert event.actor_id == ""
        assert event.action == AuditAction.READ
        assert event.success is True
        assert event.event_id

    def test_custom_values(self) -> None:
        event = AuditEvent(
            actor_id="user-1",
            action=AuditAction.CREATE,
            resource_type="document",
            resource_id="doc-123",
            workspace_id="ws-1",
        )
        assert event.actor_id == "user-1"
        assert event.action == AuditAction.CREATE
        assert event.resource_id == "doc-123"
        assert event.workspace_id == "ws-1"

    def test_frozen(self) -> None:
        event = AuditEvent()
        with pytest.raises(AttributeError):
            event.actor_id = "changed"  # type: ignore[misc]

    def test_unique_ids(self) -> None:
        a = AuditEvent()
        b = AuditEvent()
        assert a.event_id != b.event_id

    def test_metadata_default_empty(self) -> None:
        event = AuditEvent()
        assert event.metadata == {}
EOF

cat > backend/tests/presentation/test_rate_limiting.py << 'EOF'
"""Tests for rate limiting middleware."""
from __future__ import annotations

from tdp.presentation.http.middleware.rate_limiting import SlidingWindowRateLimiter


class TestSlidingWindowRateLimiter:
    def test_allows_within_limit(self) -> None:
        limiter = SlidingWindowRateLimiter(requests_per_minute=5)
        for _ in range(5):
            allowed, _, _ = limiter.is_allowed("c1")
            assert allowed

    def test_blocks_over_limit(self) -> None:
        limiter = SlidingWindowRateLimiter(requests_per_minute=2)
        limiter.is_allowed("c1")
        limiter.is_allowed("c1")
        allowed, remaining, _ = limiter.is_allowed("c1")
        assert not allowed
        assert remaining == 0

    def test_different_clients_independent(self) -> None:
        limiter = SlidingWindowRateLimiter(requests_per_minute=1)
        a1, _, _ = limiter.is_allowed("c1")
        a2, _, _ = limiter.is_allowed("c2")
        assert a1
        assert a2

    def test_remaining_decrements(self) -> None:
        limiter = SlidingWindowRateLimiter(requests_per_minute=3)
        _, r1, _ = limiter.is_allowed("c1")
        _, r2, _ = limiter.is_allowed("c1")
        _, r3, _ = limiter.is_allowed("c1")
        assert r1 == 2
        assert r2 == 1
        assert r3 == 0

    def test_max_requests_property(self) -> None:
        limiter = SlidingWindowRateLimiter(requests_per_minute=100)
        assert limiter.max_requests == 100
EOF

cat > backend/tests/test_config_phase1.py << 'EOF'
"""Tests for Phase 1 config additions."""
from __future__ import annotations

from tdp.config import Settings


class TestPhase1Config:
    def test_rate_limit_defaults(self) -> None:
        s = Settings(
            environment="development",
            database_path="/tmp/test.sqlite3",
            artifact_root_path="/tmp/artifacts",
        )
        assert s.rate_limit_enabled is True
        assert s.rate_limit_requests_per_minute == 60

    def test_audit_default_enabled(self) -> None:
        s = Settings(
            environment="development",
            database_path="/tmp/test.sqlite3",
            artifact_root_path="/tmp/artifacts",
        )
        assert s.audit_enabled is True

    def test_oidc_defaults_empty(self) -> None:
        s = Settings(
            environment="development",
            database_path="/tmp/test.sqlite3",
            artifact_root_path="/tmp/artifacts",
        )
        assert s.oidc_issuer == ""
        assert s.oidc_client_id == ""
        assert s.oidc_client_secret == ""

    def test_database_url_default_empty(self) -> None:
        s = Settings(
            environment="development",
            database_path="/tmp/test.sqlite3",
            artifact_root_path="/tmp/artifacts",
        )
        assert s.database_url == ""
EOF

echo ""
echo "============================================"
echo " Patch applied successfully."
echo ""
echo " New files:"
echo "   backend/src/tdp/audit/__init__.py"
echo "   backend/src/tdp/audit/model.py"
echo "   backend/src/tdp/audit/logger.py"
echo "   backend/src/tdp/audit/middleware.py"
echo "   backend/src/tdp/presentation/http/middleware/rate_limiting.py"
echo "   Dockerfile.backend"
echo "   Dockerfile.frontend"
echo "   docker-compose.yml"
echo "   docker-compose.dev.yml"
echo "   .dockerignore"
echo "   nginx.conf"
echo ""
echo " Modified files:"
echo "   backend/src/tdp/config.py"
echo "   backend/src/tdp/main.py"
echo "   Makefile"
echo "   .github/workflows/verify.yml"
echo ""
echo " Test files:"
echo "   backend/tests/test_audit.py"
echo "   backend/tests/presentation/test_rate_limiting.py"
echo "   backend/tests/test_config_phase1.py"
echo ""
echo " Next: bash scripts/audit_phase1_foundation.sh"
echo "============================================"
