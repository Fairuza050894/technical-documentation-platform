import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "src"


def _rule(source: str, selector: str) -> str:
    match = re.search(
        rf"{re.escape(selector)}\s*\{{(?P<body>.*?)\}}",
        source,
        flags=re.DOTALL,
    )
    assert match is not None
    return match.group("body")


def test_project_documentation_registry_uses_one_stable_desktop_grid() -> None:
    component = (FRONTEND / "modules" / "workbench" / "ProjectDocumentationOverview.tsx").read_text(
        encoding="utf-8"
    )
    workbench = (FRONTEND / "styles" / "modules" / "workbench.css").read_text(encoding="utf-8")

    assert 'className="documentation-readiness-registry"' in component
    assert 'className="documentation-readiness-columns"' in component

    registry = _rule(workbench, ".documentation-readiness-registry")
    columns = _rule(workbench, ".documentation-readiness-columns")
    item = _rule(workbench, ".documentation-readiness-item")

    assert "--documentation-readiness-columns:" in registry
    assert "grid-template-columns: var(--documentation-readiness-columns);" in columns
    assert "grid-template-columns: var(--documentation-readiness-columns);" in item
    assert "align-items: start;" in item

    for area in [
        "identity",
        "state",
        "summary",
        "actions",
        "details",
    ]:
        assert f"grid-area: {area};" in workbench

    assert '"identity state summary actions"' in item
    assert '"details details details details"' in item


def test_project_documentation_registry_has_explicit_responsive_reflow() -> None:
    workbench = (FRONTEND / "styles" / "modules" / "workbench.css").read_text(encoding="utf-8")

    medium = re.search(
        r"@media \(max-width: 1180px\)\s*\{(?P<body>.*?)\n\}",
        workbench,
        flags=re.DOTALL,
    )
    mobile = re.search(
        r"@media \(max-width: 760px\)\s*\{(?P<body>.*?)\n\}",
        workbench,
        flags=re.DOTALL,
    )

    assert medium is not None
    assert mobile is not None

    medium_body = medium.group("body")
    mobile_body = mobile.group("body")

    assert ".documentation-readiness-columns" in medium_body
    assert "display: none;" in medium_body
    assert '"identity state"' in medium_body
    assert '"summary actions"' in medium_body
    assert '"details details"' in medium_body

    assert '"identity"' in mobile_body
    assert '"state"' in mobile_body
    assert '"summary"' in mobile_body
    assert '"actions"' in mobile_body
    assert '"details"' in mobile_body
    assert "grid-template-columns: 1fr;" in mobile_body
