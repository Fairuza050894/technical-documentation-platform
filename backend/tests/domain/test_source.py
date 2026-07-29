from datetime import UTC, datetime

import pytest

from tdp.modules.sources.domain.errors import InvalidSourceFileNameError
from tdp.modules.sources.domain.model import (
    ArtifactKey,
    SourceChecksum,
    SourceConnection,
    SourceFileName,
    SourceId,
    SourceMediaType,
    SourceName,
    SourceProjectId,
    SourceStatus,
)


def build_source() -> SourceConnection:
    return SourceConnection.create_openapi_file(
        source_id=SourceId.new(),
        project_id=SourceProjectId.from_string("5e742f10-bdc0-4a24-b6dd-3002e875cc85"),
        name=SourceName("Commerce API"),
        original_file_name=SourceFileName("commerce.yaml"),
        media_type=SourceMediaType.YAML,
        checksum=SourceChecksum("a" * 64),
        artifact_key=ArtifactKey("source-id/source.yaml"),
        openapi_version="3.1.0",
        api_title="Commerce API",
        api_version="1.0.0",
        path_count=2,
        operation_count=3,
        now=datetime(2026, 7, 29, tzinfo=UTC),
    )


def test_source_file_name_keeps_only_safe_base_name() -> None:
    assert str(SourceFileName("folder\\commerce.yaml")) == "commerce.yaml"


def test_source_file_name_rejects_unsupported_extension() -> None:
    with pytest.raises(InvalidSourceFileNameError):
        SourceFileName("commerce.txt")


def test_source_can_be_archived() -> None:
    source = build_source()

    source.archive(now=datetime(2026, 7, 30, tzinfo=UTC))

    assert source.status is SourceStatus.ARCHIVED
    assert source.updated_at == datetime(2026, 7, 30, tzinfo=UTC)
