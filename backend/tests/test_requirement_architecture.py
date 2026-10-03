import ast
from pathlib import Path

_BACKEND_ROOT = Path(__file__).parents[1]
_REQUIREMENT_MODULE = _BACKEND_ROOT / "src" / "tdp" / "modules" / "requirements"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


def test_requirement_domain_has_no_framework_or_infrastructure_imports() -> None:
    forbidden = (
        "fastapi",
        "pydantic",
        "sqlite3",
        "tdp.modules.requirements.infrastructure",
        "tdp.modules.requirements.presentation",
    )
    violations = {
        str(path.relative_to(_BACKEND_ROOT)): sorted(
            module for module in _imports(path) if module.startswith(forbidden)
        )
        for path in (_REQUIREMENT_MODULE / "domain").glob("*.py")
    }
    assert all(not imports for imports in violations.values()), violations


def test_requirement_application_does_not_import_own_infrastructure_or_presentation() -> None:
    forbidden = (
        "tdp.modules.requirements.infrastructure",
        "tdp.modules.requirements.presentation",
    )
    violations = {
        str(path.relative_to(_BACKEND_ROOT)): sorted(
            module for module in _imports(path) if module.startswith(forbidden)
        )
        for path in (_REQUIREMENT_MODULE / "application").glob("*.py")
    }
    assert all(not imports for imports in violations.values()), violations
