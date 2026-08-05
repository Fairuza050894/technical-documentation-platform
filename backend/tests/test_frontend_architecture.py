import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "src"


def test_app_is_a_composition_root() -> None:
    app_path = FRONTEND / "app" / "App.tsx"
    source = app_path.read_text(encoding="utf-8")

    assert len(source.splitlines()) <= 340
    assert 'from "./components/AppShell"' in source
    assert 'from "./components/RouteContent"' in source
    assert 'from "./navigation"' in source
    assert "function SystemStatus" not in source
    assert "function RouteNotFound" not in source
    assert "<aside" not in source
    assert "<main" not in source


def test_global_css_is_an_explicit_import_manifest() -> None:
    globals_path = FRONTEND / "styles" / "globals.css"
    source = globals_path.read_text(encoding="utf-8")
    imports = re.findall(r'^@import "([^"]+)";$', source, flags=re.MULTILINE)

    assert imports == [
        "./foundation.css",
        "./application-shell.css",
        "./components.css",
        "./modules/overview.css",
        "./modules/workbench.css",
        "./modules/workspaces.css",
        "./modules/features.css",
        "./modules/documents.css",
    ]
    assert len(source.splitlines()) == len(imports)


def test_frontend_styles_do_not_encode_patch_history() -> None:
    offenders = []
    for path in sorted((FRONTEND / "styles").rglob("*.css")):
        if re.search(r"Patch 0009|patch 0009", path.read_text(encoding="utf-8")):
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []
