from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_scanner_presentation_does_not_access_private_service_repository() -> None:
    router = (
        BACKEND_ROOT
        / "src"
        / "tdp"
        / "modules"
        / "scanner"
        / "presentation"
        / "http"
        / "router.py"
    ).read_text(encoding="utf-8")

    assert "service._repository" not in router
