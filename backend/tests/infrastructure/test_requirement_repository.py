import sqlite3
from pathlib import Path

import pytest

from tdp.modules.requirements.domain.model import (
    RequirementRevision,
    RequirementType,
    TraceLink,
    TraceRelation,
    TraceTargetType,
)
from tdp.modules.requirements.infrastructure.sqlite_repository import (
    SqliteRequirementRepository,
)

_PROJECT_ID = "11111111-1111-4111-8111-111111111111"


def _prepare_project_table(database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE projects (id TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO projects (id) VALUES (?)", (_PROJECT_ID,))


@pytest.mark.anyio
async def test_repository_returns_latest_revision_and_history(tmp_path: Path) -> None:
    database_path = tmp_path / "tdp.db"
    _prepare_project_table(database_path)
    repository = SqliteRequirementRepository(database_path)
    original = RequirementRevision.create(
        project_id=_PROJECT_ID,
        key="REQ-001",
        requirement_type=RequirementType.SYSTEM,
        title="Validate request",
        statement="The system shall validate the request before workflow approval.",
        owner="Business Analyst",
        changed_by="Technical Writer [local:tw]",
        change_reason="Initial requirement.",
    )
    await repository.add_revision(original)
    revised = original.revise(
        title="Validate request before approval",
        statement="The system shall validate the request against configured policy before approval.",
        owner="Business Analyst",
        changed_by="Technical Writer [local:tw]",
        change_reason="Clarify configured policy.",
    )
    await repository.add_revision(revised)

    latest = await repository.get_latest(original.project_id, original.requirement_id)
    history = await repository.list_revisions(original.project_id, original.requirement_id)

    assert latest is not None
    assert latest.revision == 2
    assert [item.revision for item in history] == [1, 2]


@pytest.mark.anyio
async def test_repository_persists_trace_links_per_revision(tmp_path: Path) -> None:
    database_path = tmp_path / "tdp.db"
    _prepare_project_table(database_path)
    repository = SqliteRequirementRepository(database_path)
    revision = RequirementRevision.create(
        project_id=_PROJECT_ID,
        key="REQ-002",
        requirement_type=RequirementType.BUSINESS,
        title="Approve allowance",
        statement="Operations shall approve eligible allowance requests through the governed workflow.",
        owner="Operations",
        changed_by="Technical Writer [local:tw]",
        change_reason="Initial requirement.",
    )
    await repository.add_revision(revision)
    link = TraceLink.create(
        project_id=revision.project_id,
        requirement_revision_id=revision.revision_id,
        target_type=TraceTargetType.DOCUMENT,
        relation=TraceRelation.DOCUMENTED_BY,
        target_reference="44444444-4444-4444-8444-444444444444",
        verified=True,
        created_by="Technical Writer [local:tw]",
    )
    await repository.add_trace_link(link)

    links = await repository.list_trace_links(revision.revision_id)

    assert len(links) == 1
    assert links[0].target_reference == link.target_reference
    assert links[0].verified is True
