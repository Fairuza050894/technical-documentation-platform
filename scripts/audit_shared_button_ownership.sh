#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "frontend/src/styles" ]]; then
  printf 'ERROR: Run this script from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TS="$(date '+%Y%m%d_%H%M%S')"
REPORT="${HOME}/Downloads/technical-documentation-platform_shared_button_ownership_${TS}.txt"
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
  section "SHARED BUTTON OWNERSHIP B2A2 AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

section "Canonical button ownership"
for selector in \
  '.button {' \
  '.button:disabled {' \
  '.button--primary {' \
  '.button--primary:hover:not(:disabled) {' \
  '.button--primary:disabled {' \
  '.button--secondary {' \
  '.button--secondary:hover:not(:disabled) {' \
  '.button--quiet {' \
  '.button--quiet:hover:not(:disabled) {' \
  '.button--danger-quiet {' \
  '.button--danger-quiet:hover:not(:disabled) {'
do
  if grep -Fq "${selector}" frontend/src/styles/components.css; then
    printf 'PASS components owns %s\n' "${selector}" >> "${TMP}"
  else
    printf 'FAIL components missing %s\n' "${selector}" >> "${TMP}"
    overall=1
  fi
done

section "Legacy global button baselines removed"
for file in \
  frontend/src/styles/foundation.css \
  frontend/src/styles/modules/overview.css
do
  for pattern in \
    '^\.button[[:space:]]*\{' \
    '^\.button:disabled[[:space:]]*\{' \
    '^\.button--primary[[:space:]]*\{' \
    '^\.button--primary:hover:not\(:disabled\)[[:space:]]*\{' \
    '^\.button--primary:disabled[[:space:]]*\{' \
    '^\.button--secondary[[:space:]]*\{' \
    '^\.button--secondary:hover:not\(:disabled\)[[:space:]]*\{' \
    '^\.button--quiet[[:space:]]*\{' \
    '^\.button--quiet:hover:not\(:disabled\)[[:space:]]*\{' \
    '^\.button--danger-quiet[[:space:]]*\{' \
    '^\.button--danger-quiet:hover[^\{]*\{'
  do
    if grep -Eq "${pattern}" "${file}"; then
      printf 'FAIL %s still has global pattern %s\n' "${file}" "${pattern}" >> "${TMP}"
      overall=1
    fi
  done
done
if [[ "${overall}" -eq 0 ]]; then
  printf 'PASS legacy global button baselines are absent\n' >> "${TMP}"
fi

section "Disabled palette preservation"
for signal in \
  'opacity: 1;' \
  'border-color: var(--color-border-subtle);' \
  'color: var(--color-text-faint);' \
  'background: var(--color-surface-muted);' \
  'box-shadow: none;' \
  'background: var(--color-surface-emphasis);'
do
  if grep -Fq "${signal}" frontend/src/styles/components.css; then
    printf 'PASS %s\n' "${signal}" >> "${TMP}"
  else
    printf 'FAIL %s\n' "${signal}" >> "${TMP}"
    overall=1
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
    f"Duplicate selector names after B2A2: {len(duplicates)}\n"
    + "\n".join(f".{name}" for name in duplicates)
    + "\n",
    encoding="utf-8",
)
PY

section "Duplicate selector inventory"
cat "${COUNT_TMP}" >> "${TMP}"
duplicate_count="$(head -n 1 "${COUNT_TMP}" | awk '{print $NF}')"
if [[ "${duplicate_count}" -le 67 ]]; then
  printf 'PASS duplicate selector count reduced to %s or lower\n' "${duplicate_count}" >> "${TMP}"
else
  printf 'FAIL duplicate selector count is %s; expected 67 or lower\n' "${duplicate_count}" >> "${TMP}"
  overall=1
fi

run_block "Generate repository documentation" make docs || overall=1
run_block "Frontend architecture fitness tests" \
  uv run --project backend pytest backend/tests/test_frontend_architecture.py -q || overall=1
run_block "Focused button-state frontend tests" \
  npm --prefix frontend run test -- \
  src/modules/workspaces/WorkspaceRegistry.test.tsx \
  src/modules/projects/ProjectWorkspace.test.tsx \
  src/modules/features/FeatureWorkspace.test.tsx \
  src/modules/sources/SourceWorkspace.test.tsx \
  src/modules/catalog/ApiCatalogWorkspace.test.tsx \
  src/modules/changes/ChangesWorkspace.test.tsx \
  src/modules/documents/DocumentsWorkspace.test.tsx \
  src/modules/workbench/ProjectWorkbench.test.tsx || overall=1
run_block "Frontend lint" npm --prefix frontend run lint || overall=1
run_block "Frontend production build" npm --prefix frontend run build || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "Manual visual acceptance"
printf '%s\n' \
  "- Enabled primary buttons retain the current accent treatment." \
  "- Disabled primary buttons retain the current neutral emphasized-surface treatment." \
  "- Disabled secondary/quiet/danger controls remain visibly unavailable without disappearing." \
  "- Secondary, quiet, and danger-quiet enabled states retain their current presentation." \
  "- Catalog toolbar actions still become full-width at the current responsive breakpoint." \
  "- Workspace filter, Notice actions, page actions, and Workbench next action retain contextual layout." \
  "- No button label, click handler, disabled condition, or navigation behavior changes." \
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
  printf 'Shared button ownership audit completed successfully.\n'
else
  printf 'Shared button ownership audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
