#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "frontend/src/styles" ]]; then
  printf 'ERROR: Run this script from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TS="$(date '+%Y%m%d_%H%M%S')"
REPORT="${HOME}/Downloads/technical-documentation-platform_shared_form_ownership_${TS}.txt"
TMP="$(mktemp)"
COUNT_TMP="$(mktemp)"
trap 'rm -f "${TMP}" "${COUNT_TMP}"' EXIT
mkdir -p "${HOME}/Downloads"

section() {
  printf '\n============================================================\n%s\n============================================================\n' "$1" >> "${TMP}"
}

run_block() {
  local title="$1"
  shift
  section "${title}"
  set +e
  "$@" >> "${TMP}" 2>&1
  local rc=$?
  set -e
  printf '[exit_code=%s]\n' "${rc}" >> "${TMP}"
  return "${rc}"
}

overall=0

{
  section "SHARED FORM OWNERSHIP B2A1 AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

section "Canonical shared-form ownership"
for selector in \
  '.form-panel' \
  '.form-grid' \
  '.field' \
  '.field--wide' \
  '.form-error' \
  '.form-actions' \
  '.inline-actions'
do
  escaped="${selector//./\\.}"
  if grep -Eq "^[[:space:]]*${escaped}([[:space:]{,:]|$)" frontend/src/styles/components.css; then
    printf 'PASS components owns %s\n' "${selector}" >> "${TMP}"
  else
    printf 'FAIL components missing %s\n' "${selector}" >> "${TMP}"
    overall=1
  fi

  if grep -Eq "^[[:space:]]*${escaped}([[:space:]{,:]|$)" frontend/src/styles/foundation.css; then
    printf 'FAIL foundation still owns %s\n' "${selector}" >> "${TMP}"
    overall=1
  else
    printf 'PASS foundation does not own %s\n' "${selector}" >> "${TMP}"
  fi
done

python3 - "${COUNT_TMP}" <<'PY'
from collections import defaultdict
from pathlib import Path
import re
import sys

styles = Path("frontend/src/styles")
pattern = re.compile(r"(?<![\w-])\.([A-Za-z_][A-Za-z0-9_-]*)")
defined = defaultdict(set)
for path in styles.rglob("*.css"):
    for name in pattern.findall(path.read_text(encoding="utf-8")):
        defined[name].add(path)

duplicates = sorted(name for name, paths in defined.items() if len(paths) > 1)
Path(sys.argv[1]).write_text(
    f"Duplicate selector names after B2A1: {len(duplicates)}\n"
    + "\n".join(f".{name}" for name in duplicates)
    + "\n",
    encoding="utf-8",
)
PY

section "Duplicate selector inventory"
cat "${COUNT_TMP}" >> "${TMP}"
duplicate_count="$(head -n 1 "${COUNT_TMP}" | awk '{print $NF}')"
if [[ "${duplicate_count}" -le 71 ]]; then
  printf 'PASS duplicate selector count reduced to %s or lower\n' "${duplicate_count}" >> "${TMP}"
else
  printf 'FAIL duplicate selector count is %s; expected 71 or lower\n' "${duplicate_count}" >> "${TMP}"
  overall=1
fi

run_block "Generate repository documentation" make docs || overall=1
run_block "Frontend architecture fitness tests" \
  uv run --project backend pytest backend/tests/test_frontend_architecture.py -q || overall=1
run_block "Focused shared-form frontend tests" \
  npm --prefix frontend run test -- \
  src/modules/workspaces/WorkspaceRegistry.test.tsx \
  src/modules/projects/ProjectWorkspace.test.tsx \
  src/modules/features/FeatureWorkspace.test.tsx \
  src/modules/sources/SourceWorkspace.test.tsx \
  src/modules/changes/ChangesWorkspace.test.tsx \
  src/modules/documents/DocumentsWorkspace.test.tsx || overall=1
run_block "Frontend lint" npm --prefix frontend run lint || overall=1
run_block "Frontend production build" npm --prefix frontend run build || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "Manual visual acceptance"
printf '%s\n' \
  "- Create Workspace form keeps current two-column desktop layout and spacing." \
  "- Create Project form keeps current field hierarchy, disabled states, and action alignment." \
  "- Feature/Module form is visually unchanged." \
  "- Source import form is visually unchanged." \
  "- Changes comparison controls are visually unchanged." \
  "- Document generation/workflow forms are visually unchanged." \
  "- Validation messages keep their existing danger treatment." \
  >> "${TMP}"

section "Safety"
printf '%s\n' \
  "- This slice changes CSS ownership, architecture tests, and requirement documentation only." \
  "- No API, route, domain rule, database schema, JSX behavior, or application state is changed." \
  "- No .env values, credentials, tokens, SQLite records, or imported evidence are read." \
  "- No live or external endpoint is contacted." \
  >> "${TMP}"

mv "${TMP}" "${REPORT}"
trap - EXIT
rm -f "${COUNT_TMP}"

if [[ "${overall}" -eq 0 ]]; then
  printf 'Shared form ownership audit completed successfully.\n'
else
  printf 'Shared form ownership audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
