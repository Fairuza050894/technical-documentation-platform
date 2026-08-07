#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "frontend/src" || ! -d "backend/src" ]]; then
  printf 'ERROR: Run this script from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
DOWNLOADS_DIR="${HOME}/Downloads"
REPORT="${DOWNLOADS_DIR}/technical-documentation-platform_archived_project_read_only_${TIMESTAMP}.txt"
TMP="$(mktemp)"
trap 'rm -f "${TMP}"' EXIT
mkdir -p "${DOWNLOADS_DIR}"

section() {
  printf '\n============================================================\n' >> "${TMP}"
  printf '%s\n' "$1" >> "${TMP}"
  printf '============================================================\n' >> "${TMP}"
}

run_block() {
  local title="$1"
  shift
  section "${title}"
  set +e
  "$@" >> "${TMP}" 2>&1
  local exit_code=$?
  set -e
  printf '[exit_code=%s]\n' "${exit_code}" >> "${TMP}"
  return "${exit_code}"
}

overall=0

{
  section "ARCHIVED PROJECT READ-ONLY ACCESS AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

section "Project Registry access contract"
for signal in \
  'disabled={onOpenProject === undefined}' \
  'project.status === "ARCHIVED" ? "View workbench" : "Open workbench"' \
  'View ${project.name} workbench'
do
  if grep -Fq "${signal}" frontend/src/modules/projects/ProjectWorkspace.tsx; then
    printf 'PASS %s\n' "${signal}" >> "${TMP}"
  else
    printf 'FAIL %s\n' "${signal}" >> "${TMP}"
    overall=1
  fi
done

if grep -Fq \
  'disabled={project.status === "ARCHIVED" || onOpenProject === undefined}' \
  frontend/src/modules/projects/ProjectWorkspace.tsx
then
  printf 'FAIL archived project still disables workbench access\n' >> "${TMP}"
  overall=1
else
  printf 'PASS archived project no longer disables workbench access\n' >> "${TMP}"
fi

section "Workbench read-only contract"
for signal in \
  'aria-label="Archived project read-only status"' \
  'Existing evidence remains available in read-only mode.' \
  'New intake and lifecycle' \
  'changes are blocked.'
do
  if grep -Fq "${signal}" frontend/src/modules/workbench/ProjectWorkbench.tsx; then
    printf 'PASS %s\n' "${signal}" >> "${TMP}"
  else
    printf 'FAIL %s\n' "${signal}" >> "${TMP}"
    overall=1
  fi
done

section "Existing backend mutation boundaries"
for specification in \
  'backend/src/tdp/modules/sources/domain/errors.py:SOURCE_PROJECT_ARCHIVED' \
  'backend/src/tdp/modules/catalog/domain/errors.py:CATALOG_PROJECT_ARCHIVED' \
  'backend/src/tdp/modules/features/domain/errors.py:FEATURE_PROJECT_ARCHIVED' \
  'backend/src/tdp/modules/documents/domain/errors.py:DOCUMENT_PROJECT_ARCHIVED'
do
  path="${specification%%:*}"
  signal="${specification#*:}"
  if grep -Fq "${signal}" "${path}"; then
    printf 'PASS %s contains %s\n' "${path}" "${signal}" >> "${TMP}"
  else
    printf 'FAIL %s missing %s\n' "${path}" "${signal}" >> "${TMP}"
    overall=1
  fi
done

run_block "Generate repository documentation" make docs || overall=1
run_block "Focused frontend archived-project tests" \
  npm --prefix frontend run test -- \
  src/modules/projects/ProjectWorkspace.test.tsx \
  src/modules/workbench/ProjectWorkbench.test.tsx || overall=1
run_block "Backend archived-state contract tests" \
  uv run --project backend pytest -q \
  backend/tests/presentation/test_projects_api.py \
  backend/tests/presentation/test_sources_api.py \
  backend/tests/presentation/test_features_api.py \
  backend/tests/presentation/test_documents_api.py || overall=1
run_block "Frontend lint" npm --prefix frontend run lint || overall=1
run_block "Frontend production build" npm --prefix frontend run build || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "Manual visual acceptance"
printf '%s\n' \
  "- Archived project rows show View workbench as an enabled secondary action." \
  "- Archived project Archive action remains disabled." \
  "- Opening an archived project displays a clear warning that the project is read-only." \
  "- Overview, Features, Sources, API Catalog, Changes, and Documents remain navigable." \
  "- Existing data remains readable; mutation controls remain disabled." \
  "- No Reactivate action is present." \
  >> "${TMP}"

section "Safety"
printf '%s\n' \
  "- No API payload, route, database schema, or persisted domain model is changed." \
  "- Existing backend archived-state guards remain the mutation integrity boundary." \
  "- The audit does not read .env values, credentials, tokens, SQLite records, or imported evidence." \
  "- No live or external endpoint is contacted." \
  >> "${TMP}"

mv "${TMP}" "${REPORT}"
trap - EXIT

if [[ "${overall}" -eq 0 ]]; then
  printf 'Archived project read-only audit completed successfully.\n'
else
  printf 'Archived project read-only audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
