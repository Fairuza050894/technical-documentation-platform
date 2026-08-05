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


def test_system_status_grid_keeps_its_layout_contract() -> None:
    components_path = FRONTEND / "styles" / "components.css"
    source = components_path.read_text(encoding="utf-8")
    rule = re.search(
        r"\.system-status-grid\s*\{(?P<body>.*?)\}",
        source,
        flags=re.DOTALL,
    )

    assert rule is not None
    body = rule.group("body")
    assert "display: grid;" in body
    assert "grid-template-columns:" in body
    assert "gap: 1px;" in body
    assert "margin: 14px 0 0;" in body
    assert ".system-status-grid > div" in source
    assert ".system-status-grid dt" in source
    assert ".system-status-grid dd" in source


def test_frontend_styles_do_not_encode_patch_history() -> None:
    offenders = []
    for path in sorted((FRONTEND / "styles").rglob("*.css")):
        if re.search(r"Patch 0009|patch 0009", path.read_text(encoding="utf-8")):
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []
