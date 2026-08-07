#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "frontend/src/styles" ]]; then
  printf 'ERROR: Run this script from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
DOWNLOADS_DIR="${HOME}/Downloads"
REPORT="${DOWNLOADS_DIR}/technical-documentation-platform_css_ownership_b1_${TIMESTAMP}.txt"
TMP="$(mktemp)"
COUNT_TMP="$(mktemp)"
trap 'rm -f "${TMP}" "${COUNT_TMP}"' EXIT
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
  section "CSS OWNERSHIP B1 AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

section "Workbench canonical ownership contract"
for selector in \
  '.project-stage-navigation ol' \
  '.project-summary-grid' \
  '.project-workflow-map ol'
do
  if grep -Fq "${selector}" frontend/src/styles/modules/workbench.css; then
    printf 'PASS workbench owns %s\n' "${selector}" >> "${TMP}"
  else
    printf 'FAIL workbench missing %s\n' "${selector}" >> "${TMP}"
    overall=1
  fi

  if grep -Fq "${selector}" frontend/src/styles/modules/features.css; then
    printf 'FAIL features still declares %s\n' "${selector}" >> "${TMP}"
    overall=1
  else
    printf 'PASS features does not declare %s\n' "${selector}" >> "${TMP}"
  fi
done

section "Workbench stage density contract"
for signal in \
  'min-width: 1080px;' \
  'grid-template-columns: repeat(6, minmax(132px, 1fr)) 94px 94px;' \
  'grid-template-columns: 14px 24px minmax(0, 1fr);' \
  'gap: 6px;' \
  'padding: 10px;'
do
  if grep -Fq "${signal}" frontend/src/styles/modules/workbench.css; then
    printf 'PASS %s\n' "${signal}" >> "${TMP}"
  else
    printf 'FAIL %s\n' "${signal}" >> "${TMP}"
    overall=1
  fi
done

python3 - "${COUNT_TMP}" <<'PY'
from __future__ import annotations
import collections
import re
import sys
from pathlib import Path

styles = Path("frontend/src/styles")
pattern = re.compile(r"(?<![\w-])\.([A-Za-z_][A-Za-z0-9_-]*)")
defined = collections.defaultdict(set)

for path in styles.rglob("*.css"):
    for name in pattern.findall(path.read_text(encoding="utf-8")):
        defined[name].add(path)

duplicates = sorted(name for name, paths in defined.items() if len(paths) > 1)
Path(sys.argv[1]).write_text(
    f"Duplicate selector names after B1: {len(duplicates)}\n"
    + "\n".join(f".{name}" for name in duplicates)
    + "\n",
    encoding="utf-8",
)
PY

section "Duplicate selector inventory after B1"
cat "${COUNT_TMP}" >> "${TMP}"
duplicate_count="$(head -n 1 "${COUNT_TMP}" | awk '{print $NF}')"
if [[ "${duplicate_count}" -le 75 ]]; then
  printf 'PASS duplicate selector count reduced to %s or lower\n' "${duplicate_count}" >> "${TMP}"
else
  printf 'FAIL duplicate selector count is %s; expected 75 or lower\n' "${duplicate_count}" >> "${TMP}"
  overall=1
fi

run_block "Generate repository documentation" make docs || overall=1
run_block "Frontend architecture fitness tests" \
  uv run --project backend pytest backend/tests/test_frontend_architecture.py -q || overall=1
run_block "Focused Workbench tests" \
  npm --prefix frontend run test -- src/modules/workbench/ProjectWorkbench.test.tsx || overall=1
run_block "Frontend lint" npm --prefix frontend run lint || overall=1
run_block "Frontend production build" npm --prefix frontend run build || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "Manual visual acceptance"
printf '%s\n' \
  "- API Catalog and Documents stage labels are fully understandable at normal desktop width." \
  "- All six implemented stages plus Review and Release remain aligned in one horizontal navigation." \
  "- Horizontal scrolling remains available when the viewport cannot fit the minimum navigation width." \
  "- Five readiness cards keep the existing desktop, 1260px, and 760px behavior." \
  "- Six workflow-map steps keep their existing desktop and narrow-width behavior." \
  "- Feature/Module Registry layout is visually unchanged." \
  "- No application behavior, API, domain rule, database schema, or routing contract is changed." \
  >> "${TMP}"

section "Safety"
printf '%s\n' \
  "- This slice changes CSS ownership, documentation, and architecture fitness tests only." \
  "- No .env values, credentials, tokens, SQLite records, or imported evidence are read." \
  "- No live or external endpoint is contacted." \
  >> "${TMP}"

mv "${TMP}" "${REPORT}"
trap - EXIT
rm -f "${COUNT_TMP}"

if [[ "${overall}" -eq 0 ]]; then
  printf 'CSS ownership B1 audit completed successfully.\n'
else
  printf 'CSS ownership B1 audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
