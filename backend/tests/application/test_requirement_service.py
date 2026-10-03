from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tdp.modules.projects.domain.model import ProjectStatus
from tdp.modules.requirements.application.commands import CreateRequirementCommand
from tdp.modules.requirements.application.service import RequirementApplicationService
from tdp.modules.requirements.domain.model import TraceRelation, TraceTargetType
from tdp.modules.workspaces.domain.model import WorkspaceStatus


@pytest.mark.anyio
async def test_create_requirement_atomically_records_verified_feature_trace() -> None:
    workspace_id = "11111111-1111-4111-8111-111111111111"
    project_id = "22222222-2222-4222-8222-222222222222"
    feature_id = "33333333-3333-4333-8333-333333333333"

    requirement_repository = SimpleNamespace(
        get_latest_by_key=AsyncMock(return_value=None),
        add_revision=AsyncMock(),
    )
    project_repository = SimpleNamespace(
        get=AsyncMock(
            return_value=SimpleNamespace(
                workspace_id=workspace_id,
                status=ProjectStatus.ACTIVE,
            )
        )
    )
    workspace_repository = SimpleNamespace(
        get=AsyncMock(return_value=SimpleNamespace(status=WorkspaceStatus.ACTIVE))
    )
    feature_repository = SimpleNamespace(
        get=AsyncMock(return_value=SimpleNamespace(project_id=project_id))
    )

    service = RequirementApplicationService(
        requirement_repository,
        project_repository,
        workspace_repository,
        feature_repository,
        SimpleNamespace(),
        SimpleNamespace(),
    )

    result = await service.create(
        CreateRequirementCommand(
            workspace_id=workspace_id,
            project_id=project_id,
            key="REQ-001",
            requirement_type="SYSTEM",
            title="Validate shipment activity",
            statement="The system shall validate shipment activity before monitoring publication.",
            owner="System Analyst",
            feature_id=feature_id,
            acceptance_criteria=("Invalid activity is rejected with a deterministic reason.",),
            actor="Technical Writer [local:tw]",
            change_reason="Establish governed intent.",
        )
    )

    requirement_repository.add_revision.assert_awaited_once()
    persisted_revision, persisted_links = requirement_repository.add_revision.await_args.args
    assert persisted_revision.feature_id == feature_id
    assert len(persisted_links) == 1
    assert persisted_links[0].target_type is TraceTargetType.FEATURE
    assert persisted_links[0].relation is TraceRelation.IMPLEMENTED_BY
    assert persisted_links[0].target_reference == feature_id
    assert persisted_links[0].verified is True
    assert len(result.trace_links) == 1
    assert result.trace_links[0].target_reference == feature_id
