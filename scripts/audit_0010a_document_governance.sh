#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "backend/src/tdp/modules/documents" ]]; then
  printf 'ERROR: Run this script from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TS="$(date '+%Y%m%d_%H%M%S')"
REPORT="${HOME}/Downloads/technical-documentation-platform_0010a_document_governance_${TS}.txt"
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
  section "0010A ENTERPRISE DOCUMENT GOVERNANCE FOUNDATION AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

run_block "Focused governance tests" \
  uv run --project backend pytest \
  backend/tests/domain/test_document_governance.py \
  backend/tests/application/test_document_governance_service.py \
  backend/tests/presentation/test_document_governance_api.py \
  backend/tests/test_architecture.py -q || overall=1

section "Governance contract summary"
uv run --project backend python - <<'PY' >> "${TMP}" 2>&1 || overall=1
import sys
from pathlib import Path

sys.path.insert(0, str(Path("backend/src").resolve()))

from tdp.modules.documents.domain.governance import (
    DOCUMENT_TYPE_REGISTRY,
    DOCUMENT_TYPE_REGISTRY_SCHEMA_VERSION,
    PROJECT_DOCUMENTATION_POLICY,
    PROJECT_DOCUMENTATION_POLICY_KEY,
    ProjectDocumentRequirement,
)
from tdp.modules.documents.domain.model import DocumentType

print(f"Registry schema : {DOCUMENT_TYPE_REGISTRY_SCHEMA_VERSION}")
print(f"Policy key      : {PROJECT_DOCUMENTATION_POLICY_KEY}")
print(f"Registry total  : {len(DOCUMENT_TYPE_REGISTRY)}")
print("Registry order  : " + ", ".join(item.document_type.value for item in DOCUMENT_TYPE_REGISTRY))
print(
    "Required total  : "
    + str(
        sum(
            item.requirement is ProjectDocumentRequirement.REQUIRED
            for item in PROJECT_DOCUMENTATION_POLICY
        )
    )
)
print(
    "Supplementary   : "
    + str(
        sum(
            item.requirement is ProjectDocumentRequirement.SUPPLEMENTARY
            for item in PROJECT_DOCUMENTATION_POLICY
        )
    )
)
print(
    "System artifact excluded: "
    + str(
        DocumentType.TECHNICAL_SOURCE_OVERVIEW
        not in {item.document_type for item in DOCUMENT_TYPE_REGISTRY}
    )
)
PY

run_block "Generate repository documentation" make docs || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "0010A boundaries"
cat >> "${TMP}" <<'EOF'
- Registry/checklist rules are backend domain/application concerns.
- TECHNICAL_SOURCE_OVERVIEW remains backward compatible and receives no enterprise checklist credit.
- Feature/Module documentation taxonomy is intentionally unchanged; future mapping must be explicit.
- AVAILABLE means a persisted governed version exists; it does not mean approved or ready.
- No database migration, checklist UI, AI drafting, Evidence/Claim model, or readiness engine is introduced.
- Read endpoints remain available for archived Projects; existing mutation guards remain unchanged.
EOF

section "Safety"
cat >> "${TMP}" <<'EOF'
- Audit reads repository source/tests/docs and executes local quality gates only.
- It does not print .env files, credentials, tokens, SQLite records, imported evidence, or document contents.
- It does not contact live or external endpoints.
EOF

mv "${TMP}" "${REPORT}"
trap - EXIT

if [[ "${overall}" -eq 0 ]]; then
  printf '0010A document governance audit completed successfully.\n'
else
  printf '0010A document governance audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
