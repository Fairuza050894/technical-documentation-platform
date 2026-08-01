
#!/usr/bin/env bash
set -uo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
OUT="$HOME/Downloads"
mkdir -p "$OUT"
STAMP="$(date '+%Y%m%d_%H%M%S')"
REPORT="$OUT/technical-documentation-platform_engineering_safety_${STAMP}.txt"

run_check() {
  local title="$1"; shift
  printf '\n--- %s ---\n' "$title" >> "$REPORT"
  "$@" >> "$REPORT" 2>&1
  printf '[exit_code=%s]\n' "$?" >> "$REPORT"
}

{
  printf '============================================================\n'
  printf 'ENGINEERING SAFETY BASELINE AUDIT\n'
  printf '============================================================\n'
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$ROOT"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} > "$REPORT"

run_check "Git status" git status --short --branch
run_check "Whitespace" git diff --check
run_check "CI workflow" bash -lc 'sed -n "1,240p" .github/workflows/verify.yml'
run_check "Dependabot configuration" bash -lc 'sed -n "1,200p" .github/dependabot.yml'
run_check "Environment examples" bash -lc '
  printf "%s\n" "--- backend/.env.example ---"
  sed -n "1,200p" backend/.env.example
  printf "%s\n" "--- frontend/.env.example ---"
  sed -n "1,120p" frontend/.env.example
'
run_check "No hardcoded backend URL" bash -lc '
  if git grep -n "127\.0\.0\.1:8000" -- "frontend/src/**/*.ts" "frontend/src/**/*.tsx"; then
    exit 1
  fi
'
run_check "Identity boundary" bash -lc 'git grep -n -E "RequestPrincipal|IdentityAssurance|IdentityProvider|PrincipalDependency|identity/me" -- backend/src frontend/src docs || true'
run_check "No client actor contract" bash -lc '
  if git grep -n -E "actor: str = Field|payload\.actor|body: JSON\.stringify\(\{ actor" --     backend/src/tdp/modules/documents/presentation frontend/src/modules/documents; then
    exit 1
  fi
'
run_check "Local identity production guard" bash -lc 'git grep -n -E "restricted to development and test|environment in.*staging.*production" -- backend/src/tdp/config.py backend/tests/test_config.py'
run_check "Security headers" grep -nE "X-Content-Type-Options|X-Frame-Options|Content-Security-Policy|Permissions-Policy" \
  backend/src/tdp/presentation/http/middleware/security_headers.py \
  backend/tests/presentation/test_security_headers.py
run_check "Health contract" bash -lc 'git grep -n -E "health/live|health/ready|DependencyStatus|SQLite connection succeeded" -- backend/src backend/tests README.md'
run_check "Security policy" bash -lc 'sed -n "1,240p" SECURITY.md'
run_check "Ruff" uv run --project backend ruff check backend
run_check "Ruff formatting" uv run --project backend ruff format --check backend
run_check "Mypy" uv run --project backend mypy backend/src
run_check "Backend tests" uv run --project backend pytest backend/tests
run_check "ESLint" npm --prefix frontend run lint
run_check "Vitest" npm --prefix frontend run test
run_check "Production build" npm --prefix frontend run build

{
  printf '\nSafety: .env values, SQLite data, runtime artifacts, imported sources, generated documents, credentials, and secrets are excluded.\n'
  printf 'Report path: %s\n' "$REPORT"
} >> "$REPORT"

printf 'Engineering Safety audit completed.\n'
printf 'Report: %s\n' "$REPORT"
