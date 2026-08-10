import ast
from pathlib import Path

_BACKEND_ROOT = Path(__file__).parents[1]
_EVIDENCE_MODULE = _BACKEND_ROOT / "src" / "tdp" / "modules" / "evidence"


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


def test_evidence_domain_has_no_framework_or_infrastructure_imports() -> None:
    forbidden_prefixes = (
        "fastapi",
        "pydantic",
        "sqlite3",
        "tdp.modules.evidence.infrastructure",
        "tdp.modules.evidence.presentation",
    )
    violations = {
        str(path.relative_to(_BACKEND_ROOT)): sorted(
            module for module in imported_modules(path) if module.startswith(forbidden_prefixes)
        )
        for path in (_EVIDENCE_MODULE / "domain").glob("*.py")
    }
    assert all(not imports for imports in violations.values()), violations


def test_evidence_application_does_not_import_infrastructure_or_presentation() -> None:
    forbidden_prefixes = (
        "tdp.modules.evidence.infrastructure",
        "tdp.modules.evidence.presentation",
    )
    violations = {
        str(path.relative_to(_BACKEND_ROOT)): sorted(
            module for module in imported_modules(path) if module.startswith(forbidden_prefixes)
        )
        for path in (_EVIDENCE_MODULE / "application").glob("*.py")
    }
    assert all(not imports for imports in violations.values()), violations


def test_evidence_domain_does_not_depend_on_document_governance() -> None:
    imports = set()
    for path in (_EVIDENCE_MODULE / "domain").glob("*.py"):
        imports.update(imported_modules(path))

    assert not any(module.startswith("tdp.modules.documents") for module in imports)
