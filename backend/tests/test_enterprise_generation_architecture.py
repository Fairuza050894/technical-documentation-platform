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
