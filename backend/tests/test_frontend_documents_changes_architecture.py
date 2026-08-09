import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "src"
STYLES = FRONTEND / "styles"


def _class_owner_files(class_name: str) -> set[Path]:
    pattern = re.compile(rf"(?<![\w-])\.{re.escape(class_name)}(?![\w-])")
    owners: set[Path] = set()

    for path in STYLES.rglob("*.css"):
        if pattern.search(path.read_text(encoding="utf-8")):
            owners.add(path.relative_to(STYLES))

    return owners


def test_document_lifecycle_classes_have_one_module_owner() -> None:
    owner = Path("modules/documents.css")

    for class_name in [
        "document-section",
        "document-generation-form",
        "document-generation-status",
        "document-preview",
        "document-detail-badges",
        "document-metadata-grid",
        "document-workspace-grid",
        "document-panel",
        "workflow-timeline",
        "workflow-action-row",
        "document-preview-disclosure",
        "comparison-toolbar",
        "comparison-results",
        "comparison-summary",
        "comparison-excerpt",
        "document-revision-reason",
        "document-comparison-action",
        "document-change-filter",
        "document-checksum-text",
    ]:
        assert _class_owner_files(class_name) == {owner}


def test_documents_workspace_does_not_depend_on_source_or_catalog_module_classes() -> None:
    workspace_path = FRONTEND / "modules" / "documents" / "DocumentsWorkspace.tsx"
    workspace = workspace_path.read_text(encoding="utf-8")

    for foreign_class in [
        'className="catalog-toolbar__action"',
        'className="workspace-filter"',
        'className="checksum-text"',
    ]:
        assert foreign_class not in workspace

    for document_class in [
        'className="document-comparison-action"',
        'className="document-change-filter"',
        'className="document-checksum-text"',
    ]:
        assert document_class in workspace


def test_changes_result_card_baseline_is_module_owned() -> None:
    assert _class_owner_files("catalog-card") == {Path("modules/changes.css")}

    changes = (STYLES / "modules" / "changes.css").read_text(encoding="utf-8")
    card = re.search(
        r"\.changes-results \.catalog-card\s*\{(?P<body>.*?)\}",
        changes,
        flags=re.DOTALL,
    )
    assert card is not None

    for declaration in [
        "border: 1px solid var(--color-border-subtle);",
        "border-radius: var(--radius-small);",
        "box-shadow: none;",
    ]:
        assert declaration in card.group("body")


def test_document_effective_visual_contract_is_preserved() -> None:
    documents = (STYLES / "modules" / "documents.css").read_text(encoding="utf-8")

    comparison_toolbar = re.search(
        r"\.comparison-toolbar\s*\{(?P<body>.*?)\}",
        documents,
        flags=re.DOTALL,
    )
    assert comparison_toolbar is not None
    for declaration in [
        "grid-template-columns: repeat(2, minmax(210px, 1fr)) auto;",
        "gap: 12px;",
        "margin-top: 14px;",
        "padding: 16px;",
        "border-radius: var(--radius-medium);",
        "background: var(--color-surface-subtle);",
        "box-shadow: none;",
    ]:
        assert declaration in comparison_toolbar.group("body")

    metadata = re.search(
        r"\.document-metadata-grid\s*\{(?P<body>.*?)\}",
        documents,
        flags=re.DOTALL,
    )
    assert metadata is not None
    for declaration in [
        "grid-template-columns: repeat(3, minmax(0, 1fr));",
        "gap: 0;",
        "border-radius: var(--radius-small);",
    ]:
        assert declaration in metadata.group("body")

    assert "@media (max-width: 980px)" in documents
    assert "@media (max-width: 760px)" in documents
    assert "@media (max-width: 640px)" in documents


def test_global_layers_no_longer_own_document_composition() -> None:
    foundation = (STYLES / "foundation.css").read_text(encoding="utf-8")
    components = (STYLES / "components.css").read_text(encoding="utf-8")
    overview = (STYLES / "modules" / "overview.css").read_text(encoding="utf-8")

    forbidden = [
        ".document-section",
        ".document-generation-form",
        ".document-generation-status",
        ".document-preview",
        ".document-detail-badges",
        ".document-metadata-grid",
        ".document-workspace-grid",
        ".document-panel",
        ".workflow-timeline",
        ".workflow-action-row",
        ".document-preview-disclosure",
        ".comparison-toolbar",
        ".comparison-results",
        ".comparison-summary",
        ".comparison-excerpt",
        ".document-revision-reason",
    ]

    for class_name in forbidden:
        pattern = re.compile(rf"(?<![\w-]){re.escape(class_name)}(?![\w-])")
        assert pattern.search(foundation) is None
        assert pattern.search(components) is None
        assert pattern.search(overview) is None
