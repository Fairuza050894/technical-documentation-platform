#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "frontend/src" ]]; then
  printf 'ERROR: Run this script from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TS="$(date '+%Y%m%d_%H%M%S')"
REPORT="${HOME}/Downloads/technical-documentation-platform_b4_cross_route_acceptance_${TS}.txt"
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
  section "B4 FINAL CROSS-ROUTE FRONTEND ACCEPTANCE"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

run_block "Focused navigation/context frontend tests" \
  npm --prefix frontend run test -- \
  src/app/App.test.tsx \
  src/app/router.test.ts \
  src/app/navigation.test.ts \
  src/modules/workbench/ProjectWorkbench.test.tsx \
  src/modules/workspaces/WorkspaceSwitcher.test.tsx \
  src/modules/projects/ProjectWorkspace.test.tsx || overall=1

run_block "Focused cross-route workspace tests" \
  npm --prefix frontend run test -- \
  src/modules/overview/OperationalOverview.test.tsx \
  src/modules/features/FeatureWorkspace.test.tsx \
  src/modules/sources/SourceWorkspace.test.tsx \
  src/modules/catalog/ApiCatalogWorkspace.test.tsx \
  src/modules/changes/ChangesWorkspace.test.tsx \
  src/modules/documents/DocumentsWorkspace.test.tsx || overall=1

python3 - "${COUNT_TMP}" <<'PY'
from collections import defaultdict
from pathlib import Path
import re
import sys

styles = Path("frontend/src/styles")
pattern = re.compile(r"(?<![\w-])\.([A-Za-z_][A-Za-z0-9_-]*)")
defined = defaultdict(set)

for path in styles.rglob("*.css"):
    text = path.read_text(encoding="utf-8")
    for name in pattern.findall(text):
        defined[name].add(path)

duplicates = sorted(name for name, paths in defined.items() if len(paths) > 1)
Path(sys.argv[1]).write_text(
    f"Duplicate selector names at B4: {len(duplicates)}\n"
    + "\n".join(f".{name}" for name in duplicates)
    + "\n",
    encoding="utf-8",
)
PY

section "CSS duplicate-selector regression guard"
cat "${COUNT_TMP}" >> "${TMP}"
duplicate_count="$(head -n 1 "${COUNT_TMP}" | awk '{print $NF}')"
if [[ "${duplicate_count}" -le 11 ]]; then
  printf 'PASS duplicate selector count remains at %s or lower\n' "${duplicate_count}" >> "${TMP}"
else
  printf 'FAIL duplicate selector count regressed to %s; expected 11 or lower\n' "${duplicate_count}" >> "${TMP}"
  overall=1
fi

run_block "Generate repository documentation" make docs || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "Manual acceptance matrix"
cat >> "${TMP}" <<'EOF'
DESKTOP
[ ] Home / Operational Overview
[ ] Projects registry
[ ] Project Workbench Overview
[ ] Features
[ ] Sources
[ ] API Catalog
[ ] Changes
[ ] Documents
[ ] System Status

APPROXIMATELY 900 PX
[ ] Sidebar remains usable
[ ] Utility bar does not overlap content
[ ] Workspace canvas spacing remains usable
[ ] Project stage navigation remains readable/scrollable
[ ] Tables and actions remain reachable

APPROXIMATELY 760 PX
[ ] Shell uses stacked responsive presentation
[ ] Primary navigation is horizontally scrollable
[ ] Utility runtime metadata hides according to contract
[ ] System Status grid collapses to one column
[ ] Shared form grid collapses to one column
[ ] Overview / Workbench / Sources / Catalog / Changes / Documents remain usable

LONG VALUES
[ ] Long Workspace/Project names do not overlap
[ ] Long source names/checksums remain contained
[ ] Long API paths/summaries remain contained
[ ] Long feature/module names remain contained
[ ] Long document titles/revision reasons/comparison excerpts remain contained

ARCHIVED / READ-ONLY
[ ] Archived project remains visible and openable
[ ] Archived warning remains visible
[ ] Existing evidence and documentation remain readable
[ ] Mutation controls remain blocked
[ ] Archived deep links remain usable

ROUTE CONTEXT
[ ] Deep-link refresh restores Workspace + Project + stage
[ ] Feature deep-link refresh restores feature context
[ ] Browser Back restores prior route context
[ ] Browser Forward restores next route context
[ ] Workspace switch returns to selected Workspace context

B4 RULE
Any failed manual item must be documented with route, viewport, screenshot, observed result, and
expected result. Fix only demonstrated regressions; do not reopen broad ownership refactoring.
EOF

section "Safety"
printf '%s\n' \
  "- B4 is an acceptance gate, not a redesign/refactor phase." \
  "- The audit performs repository-local tests/builds and static inspection only." \
  "- No .env values, credentials, tokens, SQLite records, imported evidence, or customer documents are read." \
  "- No live or external endpoint is contacted by this audit script." \
  >> "${TMP}"

mv "${TMP}" "${REPORT}"
trap - EXIT
rm -f "${COUNT_TMP}"

if [[ "${overall}" -eq 0 ]]; then
  printf 'B4 cross-route acceptance audit completed successfully.\n'
else
  printf 'B4 cross-route acceptance audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
