import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STYLES = ROOT / "frontend" / "src" / "styles"


def _media_body(source: str, max_width: int) -> str:
    marker = f"@media (max-width: {max_width}px)"
    start = source.find(marker)
    assert start >= 0

    brace = source.find("{", start)
    assert brace >= 0

    depth = 1
    cursor = brace + 1
    while cursor < len(source) and depth:
        if source[cursor] == "{":
            depth += 1
        elif source[cursor] == "}":
            depth -= 1
        cursor += 1

    assert depth == 0
    return source[brace + 1 : cursor - 1]


def test_900px_keeps_the_vertical_sidebar_navigation_contract() -> None:
    shell = (STYLES / "application-shell.css").read_text(encoding="utf-8")

    assert "@media (max-width: 900px)" not in shell

    responsive = _media_body(shell, 760)
    assert ".navigation-list" in responsive
    assert "display: inline-flex;" in responsive
    assert "grid-template-columns: repeat(4, minmax(0, 1fr));" not in shell


def test_stacked_shell_owns_its_border_transition_at_760px() -> None:
    shell = (STYLES / "application-shell.css").read_text(encoding="utf-8")
    responsive = _media_body(shell, 760)

    sidebar = re.search(
        r"\.sidebar\s*\{(?P<body>.*?)\}",
        responsive,
        flags=re.DOTALL,
    )
    assert sidebar is not None
    assert "border-right: 0;" in sidebar.group("body")
    assert "border-bottom: 1px solid var(--color-border-subtle);" in sidebar.group("body")


def test_notice_content_can_shrink_and_wrap_at_narrow_widths() -> None:
    components = (STYLES / "components.css").read_text(encoding="utf-8")

    notice = re.search(
        r"\.notice\s*\{(?P<body>.*?)\}",
        components,
        flags=re.DOTALL,
    )
    assert notice is not None
    assert "min-width: 0;" in notice.group("body")

    body = re.search(
        r"\.notice__body\s*\{(?P<body>.*?)\}",
        components,
        flags=re.DOTALL,
    )
    assert body is not None
    assert "min-width: 0;" in body.group("body")
    assert "overflow-wrap: anywhere;" in body.group("body")

    secondary = re.search(
        r"\.notice__body small\s*\{(?P<body>.*?)\}",
        components,
        flags=re.DOTALL,
    )
    assert secondary is not None
    assert "display: block;" in secondary.group("body")
    assert "overflow-wrap: anywhere;" in secondary.group("body")
    assert "white-space: normal;" in secondary.group("body")

    responsive = _media_body(components, 760)
    responsive_notice = re.search(
        r"\.notice\s*\{(?P<body>.*?)\}",
        responsive,
        flags=re.DOTALL,
    )
    assert responsive_notice is not None

    for declaration in [
        "width: 100%;",
        "max-width: 100%;",
        "grid-template-columns: 24px minmax(0, 1fr);",
        "padding-right: 20px;",
    ]:
        assert declaration in responsive_notice.group("body")

    assert "@media (max-width: 520px)" not in components
