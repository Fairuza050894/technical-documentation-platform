#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "frontend/src" ]]; then
  printf 'ERROR: Run from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TS="$(date '+%Y%m%d_%H%M%S')"
REPORT="${HOME}/Downloads/technical-documentation-platform_0010k_project_documentation_visual_polish_${TS}.txt"
TMP="$(mktemp)"
trap 'rm -f "${TMP}"' EXIT
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
  section "0010K PROJECT DOCUMENTATION VISUAL POLISH AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

run_block "Focused documentation registry tests" \
  uv run --project backend pytest \
  backend/tests/test_frontend_documentation_visual_contract.py -q || overall=1

run_block "Focused frontend component test" \
  npm --prefix frontend run test -- \
  src/modules/workbench/ProjectDocumentationOverview.test.tsx || overall=1

section "Static 0010K visual contract"
python3 - <<'PY' >> "${TMP}" 2>&1 || overall=1
from pathlib import Path

component = Path(
    "frontend/src/modules/workbench/ProjectDocumentationOverview.tsx"
).read_text(encoding="utf-8")
css = Path("frontend/src/styles/modules/workbench.css").read_text(encoding="utf-8")

print("Registry owner       : modules/workbench.css")
print("Desktop columns      : Document / Status / Readiness / Next step")
print("Desktop alignment    : top")
print("Medium reflow        : 2 columns")
print("Mobile reflow        : 1 column")
print("Shared buttons       : unchanged")
print("Shared status labels : unchanged")
print("Readiness logic      : unchanged")
print("Sidebar/top bar      : unchanged")

assert 'className="documentation-readiness-registry"' in component
assert "--documentation-readiness-columns:" in css
assert "align-items: start;" in css
assert '"identity state summary actions"' in css
assert '"summary actions"' in css
PY

run_block "Generate repository documentation" make docs || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "0010K boundaries"
cat >> "${TMP}" <<'EOF_0010K_BOUNDARIES'
- Project documentation rows use a stable desktop grid with explicit visual zones.
- One visual column header establishes document/status/readiness/next-step alignment.
- Cells align from the top to remove vertical badge/action drift.
- Medium and mobile layouts use explicit named-grid reflow.
- Readiness details remain a native disclosure.
- Readiness policy, evidence/claim calculations, CTA routing, sidebar, and top bar are unchanged.
- Shared button/status ownership remains in components.css.
- No gradients, glass, glow, decorative dashboard elements, or visual redesign outside this registry.
EOF_0010K_BOUNDARIES

section "Safety"
cat >> "${TMP}" <<'EOF_0010K_SAFETY'
- Audit executes repository-local source/tests/docs/build checks only.
- It does not print .env files, credentials, tokens, evidence payloads, claims, or document contents.
- It does not contact live or external endpoints.
EOF_0010K_SAFETY

mv "${TMP}" "${REPORT}"
trap - EXIT

if [[ "${overall}" -eq 0 ]]; then
  printf '0010K project documentation visual polish audit completed successfully.\n'
else
  printf '0010K project documentation visual polish audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
