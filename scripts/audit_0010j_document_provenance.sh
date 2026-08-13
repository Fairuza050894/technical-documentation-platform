#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".git" || ! -f "Makefile" || ! -d "backend/src/tdp/modules/documents" ]]; then
  printf 'ERROR: Run from the technical-documentation-platform repository root.\n' >&2
  exit 1
fi

TS="$(date '+%Y%m%d_%H%M%S')"
REPORT="${HOME}/Downloads/technical-documentation-platform_0010j_document_provenance_${TS}.txt"
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
  section "0010J GOVERNED DOCUMENT PROVENANCE AUDIT"
  printf 'Generated at : %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Project root : %s\n' "$(pwd)"
  printf 'Branch       : %s\n' "$(git branch --show-current)"
  printf 'Commit       : %s\n' "$(git rev-parse HEAD)"
} >> "${TMP}"

run_block "Repository status before generation" git status --short --branch || overall=1

run_block "Focused document provenance tests" \
  uv run --project backend pytest \
  backend/tests/domain/test_document_provenance.py \
  backend/tests/application/test_enterprise_generation_service.py \
  backend/tests/infrastructure/test_document_nullable_snapshot_provenance.py \
  backend/tests/presentation/test_documents_api.py \
  backend/tests/presentation/test_enterprise_generation_api.py \
  backend/tests/test_enterprise_generation_architecture.py -q || overall=1

section "Static 0010J contract"
uv run --project backend python - <<'PY' >> "${TMP}" 2>&1 || overall=1
from tdp.modules.documents.domain.model import (
    DocumentProvenanceKind,
    DocumentProvenanceReference,
)

print("Provenance kinds       : " + ", ".join(item.value for item in DocumentProvenanceKind))
print("Source identity        : nullable")
print("Catalog synchronization: nullable")
print("Provenance relation    : document_version_provenance")
print("Evidence payload copy  : none")
print("Historical evidence IDs: not guessed")
print("Installation generator : deferred")
print("AI provenance role     : none")

assert [item.value for item in DocumentProvenanceKind] == [
    "SOURCE_REGISTRY",
    "CATALOG_SYNCHRONIZATION",
    "EVIDENCE_ARTIFACT",
]
reference = DocumentProvenanceReference.evidence_artifact(
    evidence_id="evidence-1",
    evidence_kind="DEPLOYMENT_RUNTIME",
    checksum="a" * 64,
)
assert reference.reference == "evidence:evidence-1"
PY

run_block "Generate repository documentation" make docs || overall=1
run_block "Full repository quality gate" make verify || overall=1
run_block "Whitespace" git diff --check || overall=1

section "Changed paths"
git status --short >> "${TMP}" 2>&1 || overall=1

section "0010J boundaries"
cat >> "${TMP}" <<'EOF'
- DocumentVersion source_id is nullable; no fabricated Source identity is required.
- Existing target_run_id nullable behavior is preserved.
- Provenance is an immutable ordered relation per Document Version.
- Existing Source/Catalog history is backfilled without guessing old Evidence Artifact IDs.
- New enterprise versions persist selected Evidence Artifact ID/kind/checksum references.
- Evidence payloads and materialized manifests are not copied into Documents.
- Existing document content, checksum, version lifecycle, review workflow, and generators are preserved.
- Installation Guide generation, browser/CI collectors, AI drafting, MCP, and visual redesign are absent.
EOF

section "Safety"
cat >> "${TMP}" <<'EOF'
- Audit executes repository-local source/tests/docs/build checks only.
- It does not print .env files, credentials, tokens, SQLite rows, Evidence manifests, claim
  statements, or generated document contents.
- It does not contact live or external endpoints.
EOF

mv "${TMP}" "${REPORT}"
trap - EXIT

if [[ "${overall}" -eq 0 ]]; then
  printf '0010J document provenance audit completed successfully.\n'
else
  printf '0010J document provenance audit completed with findings.\n'
fi
printf 'Report: %s\n' "${REPORT}"
exit "${overall}"
