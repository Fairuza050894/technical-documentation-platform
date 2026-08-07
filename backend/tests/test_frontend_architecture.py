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
        "./modules/changes.css",
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


def test_changes_workspace_keeps_its_visual_contract() -> None:
    workspace_path = FRONTEND / "modules" / "changes" / "ChangesWorkspace.tsx"
    styles_path = FRONTEND / "styles" / "modules" / "changes.css"
    workspace = workspace_path.read_text(encoding="utf-8")
    styles = styles_path.read_text(encoding="utf-8")

    assert 'className="content-section changes-results"' in workspace
    for selector in [
        ".changes-results .status-grid",
        ".changes-results .status-card",
        ".changes-results .catalog-list",
        ".changes-results .catalog-card__heading",
        ".changes-results .method-badge",
        ".changes-results .detail-list",
        ".changes-results .detail-list code",
    ]:
        assert selector in styles

    assert "min-height: 0;" in styles
    assert "overflow-wrap: anywhere;" in styles
    assert "@media (max-width: 760px)" in styles


def test_literal_class_names_have_css_contracts() -> None:
    literal_class_pattern = re.compile(r'className\s*=\s*["\']([^"\']+)["\']')
    css_class_pattern = re.compile(r"(?<![\w-])\.([A-Za-z_][A-Za-z0-9_-]*)")

    used_classes = set()
    for path in sorted(FRONTEND.rglob("*.tsx")):
        source = path.read_text(encoding="utf-8")
        for class_value in literal_class_pattern.findall(source):
            used_classes.update(
                token
                for token in class_value.split()
                if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", token)
            )

    defined_classes = set()
    for path in sorted((FRONTEND / "styles").rglob("*.css")):
        defined_classes.update(css_class_pattern.findall(path.read_text(encoding="utf-8")))

    assert sorted(used_classes - defined_classes) == []


def test_workbench_owns_project_navigation_and_readiness_layout() -> None:
    workbench_path = FRONTEND / "styles" / "modules" / "workbench.css"
    features_path = FRONTEND / "styles" / "modules" / "features.css"
    workbench = workbench_path.read_text(encoding="utf-8")
    features = features_path.read_text(encoding="utf-8")

    for selector in [
        ".project-stage-navigation ol",
        ".project-summary-grid",
        ".project-workflow-map ol",
    ]:
        assert selector in workbench
        assert selector not in features

    stage_navigation = re.search(
        r"\.project-stage-navigation ol\s*\{(?P<body>.*?)\}",
        workbench,
        flags=re.DOTALL,
    )
    assert stage_navigation is not None
    assert "min-width: 1080px;" in stage_navigation.group("body")
    assert "repeat(6, minmax(132px, 1fr)) 94px 94px" in stage_navigation.group("body")

    stage_button = re.search(
        r"\.project-stage-button\s*\{(?P<body>.*?)\}",
        workbench,
        flags=re.DOTALL,
    )
    assert stage_button is not None
    assert "grid-template-columns: 14px 24px minmax(0, 1fr);" in stage_button.group("body")
    assert "gap: 6px;" in stage_button.group("body")
    assert "padding: 10px;" in stage_button.group("body")

    assert "@media (max-width: 1260px)" in workbench
    assert "grid-template-columns: repeat(3, minmax(0, 1fr));" in workbench


def test_shared_forms_are_owned_by_components_layer() -> None:
    foundation_path = FRONTEND / "styles" / "foundation.css"
    components_path = FRONTEND / "styles" / "components.css"
    foundation = foundation_path.read_text(encoding="utf-8")
    components = components_path.read_text(encoding="utf-8")

    selectors = [
        ".form-panel",
        ".form-grid",
        ".field",
        ".field--wide",
        ".form-error",
        ".form-actions",
        ".inline-actions",
    ]

    for selector in selectors:
        component_rule = re.compile(
            rf"(?m)^\s*{re.escape(selector)}(?=[\s{{,:])",
        )
        assert component_rule.search(components) is not None
        assert component_rule.search(foundation) is None


def test_shared_buttons_are_owned_by_components_layer() -> None:
    foundation_path = FRONTEND / "styles" / "foundation.css"
    components_path = FRONTEND / "styles" / "components.css"
    overview_path = FRONTEND / "styles" / "modules" / "overview.css"

    foundation = foundation_path.read_text(encoding="utf-8")
    components = components_path.read_text(encoding="utf-8")
    overview = overview_path.read_text(encoding="utf-8")

    selectors = [
        ".button",
        ".button:disabled",
        ".button--primary",
        ".button--primary:hover:not(:disabled)",
        ".button--primary:disabled",
        ".button--secondary",
        ".button--secondary:hover:not(:disabled)",
        ".button--quiet",
        ".button--quiet:hover:not(:disabled)",
        ".button--danger-quiet",
        ".button--danger-quiet:hover:not(:disabled)",
    ]

    for selector in selectors:
        global_rule = re.compile(
            rf"(?m)^\s*{re.escape(selector)}\s*\{{",
        )
        assert global_rule.search(components) is not None
        assert global_rule.search(foundation) is None
        assert global_rule.search(overview) is None

    disabled = re.search(
        r"\.button:disabled\s*\{(?P<body>.*?)\}",
        components,
        flags=re.DOTALL,
    )
    assert disabled is not None
    for declaration in [
        "opacity: 1;",
        "border-color: var(--color-border-subtle);",
        "color: var(--color-text-faint);",
        "background: var(--color-surface-muted);",
        "box-shadow: none;",
    ]:
        assert declaration in disabled.group("body")

    primary_disabled = re.search(
        r"\.button--primary:disabled\s*\{(?P<body>.*?)\}",
        components,
        flags=re.DOTALL,
    )
    assert primary_disabled is not None
    assert "background: var(--color-surface-emphasis);" in primary_disabled.group("body")


def test_frontend_styles_do_not_encode_patch_history() -> None:
    offenders = []
    for path in sorted((FRONTEND / "styles").rglob("*.css")):
        if re.search(r"Patch 0009|patch 0009", path.read_text(encoding="utf-8")):
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []
