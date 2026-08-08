import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STYLES = ROOT / "frontend" / "src" / "styles"


def _has_class_selector(source: str, selector: str) -> bool:
    return (
        re.search(
            rf"(?m)^\s*{re.escape(selector)}(?=[\s{{,:])",
            source,
        )
        is not None
    )


def test_components_owns_shared_feedback_and_status_primitives() -> None:
    components = (STYLES / "components.css").read_text(encoding="utf-8")

    for selector in [
        ".notice",
        ".notice--error",
        ".notice--warning",
        ".notice__icon",
        ".notice__body",
        ".environment-badge",
        ".environment-badge__dot",
        ".environment-badge--success",
        ".status-label",
        ".record-count",
        ".status-indicator",
        ".status-indicator--success",
        ".status-indicator--neutral",
        ".status-badge",
        ".status-badge--draft",
        ".status-badge--in_review",
        ".status-badge--changes_requested",
        ".status-badge--approved",
        ".status-badge--superseded",
        ".change-kind",
        ".change-kind--added",
        ".change-kind--modified",
        ".change-kind--removed",
    ]:
        assert _has_class_selector(components, selector)


def test_legacy_layers_do_not_own_shared_feedback_and_status_baselines() -> None:
    foundation = (STYLES / "foundation.css").read_text(encoding="utf-8")
    overview = (STYLES / "modules" / "overview.css").read_text(encoding="utf-8")
    shell = (STYLES / "application-shell.css").read_text(encoding="utf-8")

    for selector in [
        ".notice",
        ".notice--error",
        ".environment-badge",
        ".status-label",
        ".record-count",
        ".status-indicator",
        ".status-indicator--success",
        ".status-indicator--neutral",
        ".status-badge",
        ".status-badge--draft",
        ".status-badge--in_review",
        ".status-badge--changes_requested",
        ".status-badge--approved",
        ".status-badge--superseded",
        ".change-kind",
        ".change-kind--added",
        ".change-kind--modified",
        ".change-kind--removed",
    ]:
        assert not _has_class_selector(foundation, selector)

    for selector in [
        ".notice",
        ".notice--error",
        ".notice__icon",
        ".notice__body",
        ".environment-badge",
        ".status-badge--superseded",
    ]:
        assert not _has_class_selector(overview, selector)

    assert ".environment-badge__dot" not in shell
    assert ".environment-badge--success .environment-badge__dot" not in shell


def test_feedback_status_effective_visual_contract_is_preserved() -> None:
    components = (STYLES / "components.css").read_text(encoding="utf-8")
    changes = (STYLES / "modules" / "changes.css").read_text(encoding="utf-8")

    notice = re.search(
        r"\.notice\s*\{(?P<body>.*?)\}",
        components,
        flags=re.DOTALL,
    )
    assert notice is not None
    for declaration in [
        "display: grid;",
        "grid-template-columns: 24px minmax(0, 1fr) auto;",
        "margin: 0 0 16px;",
        "border-left-width: 3px;",
        "font-size: 14px;",
    ]:
        assert declaration in notice.group("body")

    environment = re.search(
        r"\.environment-badge\s*\{(?P<body>.*?)\}",
        components,
        flags=re.DOTALL,
    )
    assert environment is not None
    assert "width: fit-content;" in environment.group("body")
    assert "max-width: 100%;" in environment.group("body")
    assert "flex: 0 0 auto;" in environment.group("body")

    superseded = re.search(
        r"\.status-badge--superseded\s*\{(?P<body>.*?)\}",
        components,
        flags=re.DOTALL,
    )
    assert superseded is not None
    assert "background: var(--color-surface-muted);" in superseded.group("body")
    assert "color: var(--color-text-secondary);" in superseded.group("body")

    assert ".changes-results .catalog-card__heading .status-indicator" in changes
