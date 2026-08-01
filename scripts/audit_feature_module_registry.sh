#!/usr/bin/env bash
set -uo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
OUT="$HOME/Downloads"
mkdir -p "$OUT"
STAMP="$(date '+%Y%m%d_%H%M%S')"
REPORT="$OUT/technical-documentation-platform_feature_module_registry_${STAMP}.txt"

run_check() {
  local title="$1"; shift
  printf '\n--- %s ---\n' "$title" >> "$REPORT"
  "$@" >> "$REPORT" 2>&1
  printf '[exit_code=%s]\n' "$?" >> "$REPORT"
}

{
  printf '============================================================\n'
  printf 'FEATURE / MODULE REGISTRY AND DOCUMENTATION MAP AUDIT\n'
  printf '============================================================\n'
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$ROOT"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} > "$REPORT"

run_check "Git status" git status --short --branch
run_check "Whitespace" git diff --check
run_check "Feature module inventory" bash -lc 'find backend/src/tdp/modules/features frontend/src/modules/features -type f -not -path "*/__pycache__/*" | sort'
run_check "Feature API contract" bash -lc 'git grep -n -E "features|documentation-map|FeatureResponse|CreateFeatureRequest" -- backend/src/tdp/modules/features backend/src/tdp/main.py || true'
run_check "Additive SQLite tables" bash -lc 'git grep -n -E "CREATE TABLE IF NOT EXISTS features|feature_documentation_map|UNIQUE\(project_id, feature_key\)|policy_key" -- backend/src/tdp/modules/features || true'
run_check "Deterministic baseline policy" bash -lc 'git grep -n -E "feature-documentation-baseline-v1|DocumentationRequirement|BUSINESS_REQUIREMENT|SYSTEM_REQUIREMENTS_SPECIFICATION" -- backend/src/tdp/modules/features docs || true'
run_check "Feature-scoped routes" bash -lc 'git grep -n -E "features/:featureId|workbench/features|featureId|stage: \"features\"" -- frontend/src/app frontend/src/modules/workbench frontend/src/modules/features README.md || true'
run_check "No document schema rewrite" bash -lc 'git diff -- backend/src/tdp/modules/documents/infrastructure/sqlite_repository.py backend/src/tdp/modules/documents/domain/model.py'
run_check "Ruff" uv run --project backend ruff check backend
run_check "Ruff formatting" uv run --project backend ruff format --check backend
run_check "Mypy" uv run --project backend mypy backend/src
run_check "Backend tests" uv run --project backend pytest backend/tests
run_check "ESLint" npm --prefix frontend run lint
run_check "Vitest" npm --prefix frontend run test
run_check "Production build" npm --prefix frontend run build

{
  printf '\nSafety: .env, SQLite data, runtime artifacts, imported sources, generated documents, and secrets are excluded.\n'
  printf 'Report path: %s\n' "$REPORT"
} >> "$REPORT"

printf 'Feature / Module Registry audit completed.\n'
printf 'Report: %s\n' "$REPORT"
