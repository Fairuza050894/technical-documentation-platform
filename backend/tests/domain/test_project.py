from datetime import UTC, datetime

import pytest

from tdp.modules.projects.domain.errors import (
    InvalidProjectKeyError,
    ProjectAlreadyArchivedError,
)
from tdp.modules.projects.domain.model import (
    Project,
    ProjectDescription,
    ProjectKey,
    ProjectName,
    ProjectStatus,
    WorkspaceType,
)


def test_project_key_is_normalized() -> None:
    assert str(ProjectKey(" docs-01 ")) == "DOCS-01"


def test_project_key_rejects_invalid_format() -> None:
    with pytest.raises(InvalidProjectKeyError):
        ProjectKey("invalid key")


def test_archive_changes_project_status_and_timestamp() -> None:
    created_at = datetime(2026, 7, 29, tzinfo=UTC)
    archived_at = datetime(2026, 7, 30, tzinfo=UTC)
    project = Project.create(
        key=ProjectKey("DOCS"),
        name=ProjectName("Documentation Platform"),
        description=ProjectDescription("Local project"),
        workspace_type=WorkspaceType.PERSONAL,
        now=created_at,
    )

    project.archive(now=archived_at)

    assert project.status is ProjectStatus.ARCHIVED
    assert project.updated_at == archived_at


def test_archive_rejects_second_attempt() -> None:
    project = Project.create(
        key=ProjectKey("DOCS"),
        name=ProjectName("Documentation Platform"),
        description=ProjectDescription(""),
        workspace_type=WorkspaceType.PERSONAL,
    )
    project.archive()

    with pytest.raises(ProjectAlreadyArchivedError):
        project.archive()
