import pytest

from tdp.modules.documents.domain.comparison import (
    DeterministicMarkdownSectionComparator,
    DocumentSectionChangeKind,
)
from tdp.modules.documents.domain.errors import InvalidDocumentVersionComparisonError


def test_markdown_comparator_classifies_section_changes_deterministically() -> None:
    comparator = DeterministicMarkdownSectionComparator()

    result = comparator.compare(
        baseline_version_id="baseline-version",
        target_version_id="target-version",
        document_id="document-id",
        baseline_content=(
            "# Overview\n\n"
            "## API summary\n\nTwo operations.\n\n"
            "## Removed section\n\nLegacy content.\n"
        ),
        target_content=(
            "# Overview\n\n"
            "## API summary\n\nThree operations.\n\n"
            "## Added section\n\nCurrent content.\n"
        ),
    )

    assert result.added_total == 1
    assert result.modified_total == 1
    assert result.removed_total == 1
    assert [change.kind for change in result.changes] == [
        DocumentSectionChangeKind.ADDED,
        DocumentSectionChangeKind.MODIFIED,
        DocumentSectionChangeKind.REMOVED,
    ]
    assert result.changes[1].section_key == "api-summary"
    assert result.changes[1].before_checksum != result.changes[1].after_checksum


def test_markdown_comparator_rejects_same_version() -> None:
    comparator = DeterministicMarkdownSectionComparator()

    with pytest.raises(InvalidDocumentVersionComparisonError):
        comparator.compare(
            baseline_version_id="same-version",
            target_version_id="same-version",
            document_id="document-id",
            baseline_content="# Overview\n",
            target_content="# Overview\n",
        )
