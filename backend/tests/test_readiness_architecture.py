import ast
from pathlib import Path

_BACKEND_ROOT = Path(__file__).parents[1]
_READINESS_MODULE = _BACKEND_ROOT / "src" / "tdp" / "modules" / "readiness"


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


def test_readiness_domain_is_framework_and_cross_context_independent() -> None:
    framework_prefixes = ("fastapi", "pydantic", "sqlite3")

    def is_forbidden(module: str) -> bool:
        if module.startswith(framework_prefixes):
            return True
        return module.startswith("tdp.modules.") and not module.startswith("tdp.modules.readiness.")

    violations = {
        str(path.relative_to(_BACKEND_ROOT)): sorted(
            module for module in imported_modules(path) if is_forbidden(module)
        )
        for path in (_READINESS_MODULE / "domain").glob("*.py")
    }
    assert all(not imports for imports in violations.values()), violations


def test_readiness_application_does_not_depend_on_infrastructure_or_presentation() -> None:
    forbidden_fragments = (
        ".infrastructure",
        ".presentation",
    )
    violations = {
        str(path.relative_to(_BACKEND_ROOT)): sorted(
            module
            for module in imported_modules(path)
            if module.startswith("tdp.modules.")
            and any(fragment in module for fragment in forbidden_fragments)
        )
        for path in (_READINESS_MODULE / "application").glob("*.py")
    }
    assert all(not imports for imports in violations.values()), violations


def test_readiness_has_no_persistence_adapter() -> None:
    assert not (_READINESS_MODULE / "infrastructure").exists()
