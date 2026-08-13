import ast
from pathlib import Path

_BACKEND = Path(__file__).parents[1]
_DOCUMENTS = _BACKEND / "src" / "tdp" / "modules" / "documents"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


def test_enterprise_generation_domain_has_no_cross_context_dependency() -> None:
    imports = _imports(_DOCUMENTS / "domain" / "generation.py")
    forbidden = (
        "fastapi",
        "pydantic",
        "sqlite3",
        "tdp.modules.catalog",
        "tdp.modules.evidence",
        "tdp.modules.projects",
        "tdp.modules.readiness",
        "tdp.modules.sources",
        "tdp.modules.workspaces",
    )
    assert not any(module.startswith(forbidden) for module in imports)


def test_enterprise_generation_application_depends_on_ports_not_infrastructure() -> None:
    paths = (
        _DOCUMENTS / "application" / "enterprise_generation_ports.py",
        _DOCUMENTS / "application" / "enterprise_generation_service.py",
    )
    imports = {module for path in paths for module in _imports(path)}
    assert not any(".infrastructure" in module for module in imports)
    assert not any(".presentation" in module for module in imports)
    assert not any(module.startswith("tdp.modules.readiness") for module in imports)
    assert not any(module.startswith("tdp.modules.evidence") for module in imports)


def test_cross_context_collection_is_isolated_in_documents_infrastructure() -> None:
    adapter = _DOCUMENTS / "infrastructure" / "enterprise_generation_inputs.py"
    imports = _imports(adapter)
    assert "tdp.modules.readiness.application.service" in imports
    assert "tdp.modules.evidence.domain.repository" in imports
    assert "tdp.modules.catalog.domain.repository" in imports


def test_legacy_technical_source_overview_route_remains_available() -> None:
    router = (_DOCUMENTS / "presentation" / "http" / "router.py").read_text(encoding="utf-8")
    service = (_DOCUMENTS / "application" / "service.py").read_text(encoding="utf-8")
    assert "/documents/technical-source-overview" in router
    assert "GenerateTechnicalSourceOverviewCommand" in service


def test_as_built_extension_does_not_create_a_parallel_generation_service() -> None:
    service = (_DOCUMENTS / "application" / "enterprise_generation_service.py").read_text(
        encoding="utf-8"
    )
    adapter = (_DOCUMENTS / "infrastructure" / "enterprise_generation_inputs.py").read_text(
        encoding="utf-8"
    )

    assert "GenerateAsBuilt" not in service
    assert "DocumentType.AS_BUILT" not in service
    assert "AS_BUILT" not in adapter


def test_hld_evidence_selection_remains_generic_and_does_not_recreate_readiness_policy() -> None:
    service = (_DOCUMENTS / "application" / "enterprise_generation_service.py").read_text(
        encoding="utf-8"
    )
    adapter = (_DOCUMENTS / "infrastructure" / "enterprise_generation_inputs.py").read_text(
        encoding="utf-8"
    )

    assert "DocumentType.HLD" not in service
    assert "DocumentType.HLD" not in adapter
    assert "profile.accepted_evidence_kinds" in adapter
    assert "EvidenceKind.CATALOG_SNAPSHOT" in adapter
    assert "EvidenceKind.SOURCE_ARTIFACT" in adapter
    assert "HLD_TECHNICAL_EVIDENCE_REQUIRED" not in adapter


def test_document_provenance_is_generalized_end_to_end() -> None:
    repository_root = _BACKEND.parent
    model = (_DOCUMENTS / "domain" / "model.py").read_text(encoding="utf-8")
    dto = (_DOCUMENTS / "application" / "dto.py").read_text(encoding="utf-8")
    router = (_DOCUMENTS / "presentation" / "http" / "router.py").read_text(encoding="utf-8")
    repository = (_DOCUMENTS / "infrastructure" / "sqlite_repository.py").read_text(
        encoding="utf-8"
    )
    frontend_types = (
        repository_root / "frontend" / "src" / "modules" / "documents" / "types.ts"
    ).read_text(encoding="utf-8")

    assert "source_id: str | None" in model
    assert "target_run_id: str | None" in model
    assert "DocumentProvenanceReference" in model
    assert "EVIDENCE_ARTIFACT" in model
    assert "source_id: str | None" in dto
    assert "provenance: tuple[DocumentProvenanceDto, ...]" in dto
    assert "source_id: str | None" in router
    assert "provenance: list[DocumentProvenanceResponse]" in router
    assert "source_id TEXT," in repository
    assert "target_run_id TEXT," in repository
    assert "document_version_provenance" in repository
    assert "_migrate_nullable_document_provenance" in repository
    assert "source_id: string | null" in frontend_types
    assert "DocumentProvenanceReference" in frontend_types
