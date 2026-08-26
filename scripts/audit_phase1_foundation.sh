#!/usr/bin/env bash
set -euo pipefail

REPORT=""
PASS=0
FAIL=0
WARN=0

pass() { PASS=$((PASS + 1)); REPORT+="  PASS  $1\n"; }
fail() { FAIL=$((FAIL + 1)); REPORT+="  FAIL  $1 -- $2\n"; }
warn() { WARN=$((WARN + 1)); REPORT+="  WARN  $1 -- $2\n"; }
header() { REPORT+="\n=== $1 ===\n"; }

echo "Running Phase 1 Foundation Audit..."
echo ""

header "WS 1.3 -- Audit Trail"

[ -f "backend/src/tdp/audit/__init__.py" ] \
  && pass "1.3.1 audit/__init__.py exists" \
  || fail "1.3.1 audit/__init__.py missing" "run apply script"

[ -f "backend/src/tdp/audit/model.py" ] \
  && pass "1.3.1 audit/model.py exists" \
  || fail "1.3.1 audit/model.py missing" "run apply script"

grep -q "class AuditAction" backend/src/tdp/audit/model.py 2>/dev/null \
  && pass "1.3.1 AuditAction enum defined" \
  || fail "1.3.1 AuditAction not found" "check model.py"

grep -q "class AuditEvent" backend/src/tdp/audit/model.py 2>/dev/null \
  && pass "1.3.1 AuditEvent dataclass defined" \
  || fail "1.3.1 AuditEvent not found" "check model.py"

grep -q "frozen=True" backend/src/tdp/audit/model.py 2>/dev/null \
  && pass "1.3.1 AuditEvent is immutable (frozen)" \
  || fail "1.3.1 AuditEvent not frozen" "add frozen=True"

[ -f "backend/src/tdp/audit/logger.py" ] \
  && pass "1.3.2 audit/logger.py exists" \
  || fail "1.3.2 audit/logger.py missing" "run apply script"

grep -q "class StructuredAuditLogger" backend/src/tdp/audit/logger.py 2>/dev/null \
  && pass "1.3.2 StructuredAuditLogger defined" \
  || fail "1.3.2 StructuredAuditLogger not found" "check logger.py"

[ -f "backend/src/tdp/audit/middleware.py" ] \
  && pass "1.3.3 audit/middleware.py exists" \
  || fail "1.3.3 audit/middleware.py missing" "run apply script"

grep -q "class AuditMiddleware" backend/src/tdp/audit/middleware.py 2>/dev/null \
  && pass "1.3.3 AuditMiddleware defined" \
  || fail "1.3.3 AuditMiddleware not found" "check middleware.py"

grep -q "AuditMiddleware" backend/src/tdp/main.py 2>/dev/null \
  && pass "1.3.3 AuditMiddleware wired in main.py" \
  || fail "1.3.3 AuditMiddleware not in main.py" "run apply script"

header "WS 1.4 -- Security Hardening"

[ -f "backend/src/tdp/presentation/http/middleware/rate_limiting.py" ] \
  && pass "1.4.1 rate_limiting.py exists" \
  || fail "1.4.1 rate_limiting.py missing" "run apply script"

grep -q "class RateLimitMiddleware" backend/src/tdp/presentation/http/middleware/rate_limiting.py 2>/dev/null \
  && pass "1.4.1 RateLimitMiddleware defined" \
  || fail "1.4.1 RateLimitMiddleware not found" "check rate_limiting.py"

grep -q "X-RateLimit" backend/src/tdp/presentation/http/middleware/rate_limiting.py 2>/dev/null \
  && pass "1.4.1 Rate limit headers present" \
  || fail "1.4.1 Missing X-RateLimit headers" "check rate_limiting.py"

grep -q "RateLimitMiddleware" backend/src/tdp/main.py 2>/dev/null \
  && pass "1.4.1 RateLimitMiddleware wired in main.py" \
  || fail "1.4.1 RateLimitMiddleware not in main.py" "run apply script"

grep -q "rate_limit_enabled" backend/src/tdp/config.py 2>/dev/null \
  && pass "1.4.1 rate_limit_enabled config field exists" \
  || fail "1.4.1 rate_limit_enabled missing from config" "run apply script"

grep -q "rate_limit_requests_per_minute" backend/src/tdp/config.py 2>/dev/null \
  && pass "1.4.1 rate_limit_requests_per_minute config field exists" \
  || fail "1.4.1 rate_limit_requests_per_minute missing" "run apply script"

grep -q "audit_enabled" backend/src/tdp/config.py 2>/dev/null \
  && pass "1.4.7 audit_enabled config field exists" \
  || fail "1.4.7 audit_enabled missing from config" "run apply script"

grep -q "oidc_issuer" backend/src/tdp/config.py 2>/dev/null \
  && pass "1.4.7 OIDC config fields present (future-ready)" \
  || fail "1.4.7 OIDC fields missing from config" "run apply script"

grep -q "database_url" backend/src/tdp/config.py 2>/dev/null \
  && pass "1.4.7 database_url config field present (future-ready)" \
  || fail "1.4.7 database_url missing from config" "run apply script"

header "WS 3.1 -- Containerization"

[ -f "Dockerfile.backend" ] \
  && pass "3.1.1 Dockerfile.backend exists" \
  || fail "3.1.1 Dockerfile.backend missing" "run apply script"

grep -q "USER tdp" Dockerfile.backend 2>/dev/null \
  && pass "3.1.1 Backend runs as non-root (USER tdp)" \
  || fail "3.1.1 Backend missing non-root USER" "check Dockerfile.backend"

grep -q "HEALTHCHECK" Dockerfile.backend 2>/dev/null \
  && pass "3.1.1 Backend HEALTHCHECK defined" \
  || fail "3.1.1 Backend missing HEALTHCHECK" "check Dockerfile.backend"

grep -q "AS builder" Dockerfile.backend 2>/dev/null \
  && pass "3.1.1 Backend uses multi-stage build" \
  || fail "3.1.1 Backend not multi-stage" "check Dockerfile.backend"

[ -f "Dockerfile.frontend" ] \
  && pass "3.1.2 Dockerfile.frontend exists" \
  || fail "3.1.2 Dockerfile.frontend missing" "run apply script"

grep -q "USER tdp" Dockerfile.frontend 2>/dev/null \
  && pass "3.1.2 Frontend runs as non-root" \
  || fail "3.1.2 Frontend missing non-root USER" "check Dockerfile.frontend"

[ -f "nginx.conf" ] \
  && pass "3.1.2 nginx.conf exists" \
  || fail "3.1.2 nginx.conf missing" "run apply script"

grep -q "X-Content-Type-Options" nginx.conf 2>/dev/null \
  && pass "3.1.2 nginx security headers present" \
  || fail "3.1.2 nginx missing security headers" "check nginx.conf"

grep -q "proxy_pass.*backend:8000" nginx.conf 2>/dev/null \
  && pass "3.1.2 nginx API proxy configured" \
  || fail "3.1.2 nginx API proxy missing" "check nginx.conf"

[ -f "docker-compose.yml" ] \
  && pass "3.1.3 docker-compose.yml exists" \
  || fail "3.1.3 docker-compose.yml missing" "run apply script"

[ -f "docker-compose.dev.yml" ] \
  && pass "3.1.4 docker-compose.dev.yml exists" \
  || fail "3.1.4 docker-compose.dev.yml missing" "run apply script"

[ -f ".dockerignore" ] \
  && pass "3.1.5 .dockerignore exists" \
  || fail "3.1.5 .dockerignore missing" "run apply script"

grep -q "docker:" Makefile 2>/dev/null \
  && pass "3.1.6 Makefile docker target exists" \
  || fail "3.1.6 Makefile docker target missing" "run apply script"

header "WS 3.2 -- CI Enhancement"

grep -q "pip audit" .github/workflows/verify.yml 2>/dev/null \
  && pass "3.2.1 pip audit step in CI" \
  || fail "3.2.1 pip audit missing from CI" "run apply script"

grep -q "npm audit" .github/workflows/verify.yml 2>/dev/null \
  && pass "3.2.1 npm audit step in CI" \
  || fail "3.2.1 npm audit missing from CI" "run apply script"

header "Tests"

[ -f "backend/tests/test_audit.py" ] \
  && pass "test_audit.py exists" \
  || fail "test_audit.py missing" "create test file"

[ -f "backend/tests/presentation/test_rate_limiting.py" ] \
  && pass "test_rate_limiting.py exists" \
  || fail "test_rate_limiting.py missing" "create test file"

[ -f "backend/tests/test_config_phase1.py" ] \
  && pass "test_config_phase1.py exists" \
  || fail "test_config_phase1.py missing" "create test file"

header "Lint & Type Check"

if command -v uv &>/dev/null; then
  if uv run --project backend ruff check backend/src/tdp/audit backend/src/tdp/presentation/http/middleware/rate_limiting.py 2>/dev/null; then
    pass "ruff check -- new files clean"
  else
    fail "ruff check -- violations found" "run: uv run --project backend ruff check backend"
  fi

  if uv run --project backend ruff format --check backend/src/tdp/audit backend/src/tdp/presentation/http/middleware/rate_limiting.py 2>/dev/null; then
    pass "ruff format -- new files formatted"
  else
    fail "ruff format -- formatting issues" "run: uv run --project backend ruff format backend"
  fi
else
  warn "uv not found" "skipping lint checks"
fi

header "Backend Tests"

if command -v uv &>/dev/null; then
  echo "  Running pytest..."
  TEST_OUTPUT=$(uv run --project backend pytest backend/tests/test_audit.py backend/tests/presentation/test_rate_limiting.py backend/tests/test_config_phase1.py -q 2>&1) && {
    pass "Phase 1 tests pass"
  } || {
    fail "Phase 1 tests FAIL" "$TEST_OUTPUT"
  }

  echo "  Running full test suite..."
  FULL_OUTPUT=$(uv run --project backend pytest backend/tests -q 2>&1) && {
    pass "Full test suite pass (no regressions)"
  } || {
    fail "Full test suite FAIL (regression)" "run: make test"
  }
else
  warn "uv not found" "skipping tests"
fi

echo ""
echo "============================================"
echo " PHASE 1 FOUNDATION AUDIT REPORT"
echo "============================================"
echo ""
echo -e "$REPORT"
echo "--------------------------------------------"
echo " PASS: $PASS"
echo " FAIL: $FAIL"
echo " WARN: $WARN"
echo "--------------------------------------------"

if [ "$FAIL" -gt 0 ]; then
  echo ""
  echo "RESULT: FAIL -- $FAIL check(s) did not pass."
  exit 1
else
  echo ""
  echo "RESULT: PASS -- All checks passed."
  exit 0
fi
