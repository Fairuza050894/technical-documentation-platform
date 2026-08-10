from pathlib import Path

FRONTEND = Path(__file__).parents[2] / "frontend" / "src"


def test_documentation_workbench_consumes_backend_governance_contracts() -> None:
    api = (FRONTEND / "modules" / "workbench" / "governanceApi.ts").read_text(encoding="utf-8")
    component = (FRONTEND / "modules" / "workbench" / "ProjectDocumentationOverview.tsx").read_text(
        encoding="utf-8"
    )

    for path in (
        "/documentation-checklist",
        "/readiness",
        "/evidence",
        "/claims",
    ):
        assert path in api

    assert "project-documentation-baseline-v1" not in component
    assert "document-readiness-v1" not in component
    assert "ASBUILT_OBSERVED_CLAIM_REQUIRED" not in component


def test_documentation_workbench_keeps_existing_project_stage_topology() -> None:
    router = (FRONTEND / "app" / "router.ts").read_text(encoding="utf-8")
    expected = (
        '"overview",',
        '"features",',
        '"sources",',
        '"catalog",',
        '"changes",',
        '"documents",',
    )
    for stage in expected:
        assert stage in router

    assert '"documentation",' not in router


def test_workbench_css_owns_documentation_readiness_presentation() -> None:
    workbench = (FRONTEND / "styles" / "modules" / "workbench.css").read_text(encoding="utf-8")
    required_selectors = (
        ".project-documentation-overview",
        ".documentation-governance-summary",
        ".documentation-readiness-list",
        ".documentation-readiness-item",
        ".documentation-readiness-details",
        ".documentation-traceability",
    )
    for selector in required_selectors:
        assert selector in workbench

    assert "linear-gradient" not in workbench
