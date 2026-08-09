import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STYLES = ROOT / "frontend" / "src" / "styles"


def _class_owner_files(class_name: str) -> set[Path]:
    pattern = re.compile(rf"(?<![\w-])\.{re.escape(class_name)}(?![\w-])")
    owners: set[Path] = set()

    for path in STYLES.rglob("*.css"):
        if pattern.search(path.read_text(encoding="utf-8")):
            owners.add(path.relative_to(STYLES))

    return owners


def test_source_registry_has_a_dedicated_module_owner() -> None:
    source_owner = Path("modules/sources.css")

    for class_name in [
        "workspace-filter",
        "checksum-text",
    ]:
        assert _class_owner_files(class_name) == {source_owner}


def test_api_catalog_has_a_dedicated_module_owner() -> None:
    catalog_owner = Path("modules/catalog.css")

    for class_name in [
        "catalog-toolbar",
        "catalog-toolbar__action",
        "catalog-layout",
        "catalog-row-button",
        "http-method",
        "evidence-panel",
        "evidence-list",
        "source-reference",
    ]:
        assert _class_owner_files(class_name) == {catalog_owner}


def test_existing_workspace_and_feature_module_ownership_remains_intact() -> None:
    workspaces = (STYLES / "modules" / "workspaces.css").read_text(encoding="utf-8")
    features = (STYLES / "modules" / "features.css").read_text(encoding="utf-8")

    for selector in [
        ".workspace-switcher",
        ".workspace-switcher__trigger",
        ".workspace-switcher__popover",
    ]:
        assert selector in workspaces

    for selector in [
        ".feature-workspace",
        ".feature-registry",
        ".feature-documentation-map",
        ".feature-signal-strip",
    ]:
        assert selector in features


def test_registry_intake_migration_preserves_effective_layout_contracts() -> None:
    sources = (STYLES / "modules" / "sources.css").read_text(encoding="utf-8")
    catalog = (STYLES / "modules" / "catalog.css").read_text(encoding="utf-8")

    for declaration in [
        'grid-template-areas:\n    "label blank"\n    "control action";',
        "grid-template-columns: minmax(240px, 380px) auto;",
        "max-width: 620px;",
    ]:
        assert declaration in sources

    for declaration in [
        "grid-template-columns: minmax(210px, 1fr) minmax(210px, 1fr) auto;",
        "grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.8fr);",
        "top: calc(var(--utility-height) + 16px);",
        "max-width: 180px;",
    ]:
        assert declaration in catalog

    assert "@media (max-width: 760px)" in sources
    assert "@media (max-width: 980px)" in catalog
