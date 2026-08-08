import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STYLES = ROOT / "frontend" / "src" / "styles"


def _has_rule_entry(source: str, selector: str) -> bool:
    return (
        re.search(
            rf"(?m)^\s*{re.escape(selector)}\s*(?:,|\{{)",
            source,
        )
        is not None
    )


def test_components_owns_table_and_page_primitive_baselines() -> None:
    components = (STYLES / "components.css").read_text(encoding="utf-8")

    for selector in [
        ".topbar",
        ".eyebrow",
        ".content-section",
        ".section-heading",
        ".section-heading--split",
        ".table-frame",
        ".table-secondary-text",
        ".table-action-column",
        ".empty-state",
    ]:
        assert _has_rule_entry(components, selector)

    topbar = re.search(r"\.topbar\s*\{(?P<body>.*?)\}", components, flags=re.DOTALL)
    assert topbar is not None
    for declaration in [
        "min-width: 0;",
        "flex-wrap: wrap;",
        "padding-bottom: 24px;",
        "border-bottom: 1px solid var(--color-border-subtle);",
        "scroll-margin-top: calc(var(--utility-height) + 16px);",
    ]:
        assert declaration in topbar.group("body")

    table_frame = re.search(r"\.table-frame\s*\{(?P<body>.*?)\}", components, flags=re.DOTALL)
    assert table_frame is not None
    assert "box-shadow: var(--shadow-low);" in table_frame.group("body")

    secondary = re.search(
        r"\.table-secondary-text\s*\{(?P<body>.*?)\}",
        components,
        flags=re.DOTALL,
    )
    assert secondary is not None
    for declaration in [
        "max-width: 420px;",
        "overflow: hidden;",
        "text-overflow: ellipsis;",
        "white-space: nowrap;",
    ]:
        assert declaration in secondary.group("body")

    empty_state = re.search(r"\.empty-state\s*\{(?P<body>.*?)\}", components, flags=re.DOTALL)
    assert empty_state is not None
    assert "margin-top: 18px;" in empty_state.group("body")


def test_foundation_no_longer_owns_shared_table_or_page_primitive_baselines() -> None:
    foundation = (STYLES / "foundation.css").read_text(encoding="utf-8")

    for selector in [
        ".topbar",
        ".eyebrow",
        ".content-section",
        ".section-heading--split",
        ".empty-state",
        ".table-frame",
        ".table-secondary-text",
        ".table-action-column",
    ]:
        assert not _has_rule_entry(foundation, selector)

    assert re.search(r"(?m)^\s*\.section-heading p\s*,", foundation) is None


def test_global_leakage_is_removed_and_contextual_overrides_remain() -> None:
    components = (STYLES / "components.css").read_text(encoding="utf-8")
    overview = (STYLES / "modules" / "overview.css").read_text(encoding="utf-8")
    workbench = (STYLES / "modules" / "workbench.css").read_text(encoding="utf-8")
    features = (STYLES / "modules" / "features.css").read_text(encoding="utf-8")

    assert not _has_rule_entry(overview, ".topbar")
    assert not _has_rule_entry(overview, ".table-frame th")
    assert not _has_rule_entry(overview, ".table-frame td")

    assert "@media (max-width: 760px)" in components
    assert "@media (max-width: 720px)" in components

    assert ".embedded-workspace > .content-section:first-child" in workbench
    assert ".project-workbench-header__identity > .eyebrow" in workbench
    assert ".operations-section > .empty-state" in overview
    assert ".document-section > .section-heading" in overview
    assert ".document-section .table-frame" in overview
    assert ".feature-registry .table-frame" in features
