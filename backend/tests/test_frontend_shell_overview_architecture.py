import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STYLES = ROOT / "frontend" / "src" / "styles"


def _contains_class(source: str, class_name: str) -> bool:
    pattern = re.compile(rf"(?<![\w-])\.{re.escape(class_name)}(?![\w-])")
    return pattern.search(source) is not None


def test_application_shell_is_the_canonical_shell_owner() -> None:
    foundation = (STYLES / "foundation.css").read_text(encoding="utf-8")
    shell = (STYLES / "application-shell.css").read_text(encoding="utf-8")
    overview = (STYLES / "modules" / "overview.css").read_text(encoding="utf-8")

    shell_classes = [
        "app-shell",
        "main-content",
        "sidebar",
        "sidebar-service",
        "primary-navigation",
        "navigation-group",
        "navigation-list",
        "navigation-item",
        "navigation-item__icon",
        "product-mark",
        "product-mark__symbol",
        "utility-bar",
        "utility-status__item",
        "utility-status__divider",
        "workspace-context",
        "workspace-canvas",
    ]

    for class_name in shell_classes:
        assert _contains_class(shell, class_name)
        assert not _contains_class(foundation, class_name)
        assert not _contains_class(overview, class_name)


def test_shell_responsive_contract_is_preserved_in_shell_layer() -> None:
    shell = (STYLES / "application-shell.css").read_text(encoding="utf-8")

    for breakpoint in ["980px", "900px", "760px", "640px"]:
        assert f"@media (max-width: {breakpoint})" in shell

    for declaration in [
        "grid-template-columns: 210px minmax(0, 1fr);",
        "display: block;",
        "position: relative;",
        "min-height: 46px;",
        "padding: 20px 16px 44px;",
        "padding: 22px 18px 36px;",
    ]:
        assert declaration in shell


def test_operational_overview_owns_overview_only_primitives() -> None:
    components = (STYLES / "components.css").read_text(encoding="utf-8")
    overview = (STYLES / "modules" / "overview.css").read_text(encoding="utf-8")

    for class_name in [
        "data-provenance",
        "page-actions",
        "operations-section__heading",
        "rail-section__heading",
        "signal-region__heading",
    ]:
        assert _contains_class(overview, class_name)
        assert not _contains_class(components, class_name)

    assert ".data-provenance__dot" in overview
    assert "background: #2aa66a;" in overview


def test_shared_responsive_primitives_do_not_leak_from_overview() -> None:
    components = (STYLES / "components.css").read_text(encoding="utf-8")
    overview = (STYLES / "modules" / "overview.css").read_text(encoding="utf-8")

    assert ".form-grid,\n  .system-status-grid" in components
    assert re.search(r"(?m)^\s*\.field label\s*\{", overview) is None
    assert re.search(r"(?m)^\s*\.form-grid\s*,", overview) is None
    assert ".system-status-grid" not in overview

    for selector in [
        "input,\nselect,\ntextarea",
        "input:hover,\nselect:hover,\ntextarea:hover",
    ]:
        assert selector not in overview


def test_global_accessibility_behaviour_is_foundational() -> None:
    foundation = (STYLES / "foundation.css").read_text(encoding="utf-8")
    shell = (STYLES / "application-shell.css").read_text(encoding="utf-8")
    overview = (STYLES / "modules" / "overview.css").read_text(encoding="utf-8")

    assert "color-scheme: light;" in foundation
    assert "scroll-padding-top: calc(var(--utility-height) + 16px);" in foundation
    assert "@media (prefers-reduced-motion: reduce)" in foundation
    assert "box-shadow: var(--focus-ring);" in foundation

    assert "@media (prefers-reduced-motion: reduce)" not in overview
    assert "scroll-padding-top:" not in overview
    assert "button:focus-visible" not in shell
