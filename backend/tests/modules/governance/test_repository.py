from datetime import UTC, datetime
from uuid import uuid4

from tdp.modules.governance.domain.model import (
    ChangeSurface,
    ImpactAssessment,
    RequirementRevision,
    RequirementType,
    TraceLink,
    TraceTargetType,
    WorkflowCase,
    WorkflowState,
)
from tdp.modules.governance.infrastructure.sqlite_repository import (
    SqliteGovernanceRepository,
    requirement_coverage,
)


def test_repository_persists_latest_requirement_and_traceability(tmp_path) -> None:
    repository = SqliteGovernanceRepository(tmp_path / "governance.db")
    project_id = str(uuid4())
    requirement_id = str(uuid4())
    first = RequirementRevision.create(
        project_id=project_id,
        requirement_id=requirement_id,
        revision=1,
        requirement_type=RequirementType.BUSINESS,
        title="Trace documentation",
        statement="The platform shall trace controlled documentation to requirements.",
        rationale="Reviewers need source-backed accountability.",
        created_by="Owner [local:test]",
        now=datetime(2026, 10, 3, tzinfo=UTC),
    )
    second = RequirementRevision.create(
        project_id=project_id,
        requirement_id=requirement_id,
        revision=2,
        requirement_type=RequirementType.BUSINESS,
        title="Trace released documentation",
        statement="The platform shall trace released documentation to requirements and evidence.",
        rationale="Release decisions require end-to-end traceability.",
        created_by="Owner [local:test]",
        now=datetime(2026, 10, 3, 1, tzinfo=UTC),
    )
    repository.add_requirement(first)
    repository.add_requirement(second)

    link = TraceLink.create(
        project_id=project_id,
        requirement_id=requirement_id,
        target_type=TraceTargetType.DOCUMENT,
        target_id="TDP-TSD-001",
        relation="VERIFIED_BY",
        created_by="Owner [local:test]",
    )
    repository.add_trace_link(link)

    requirements = repository.list_requirements(project_id)
    links = repository.list_trace_links(project_id)

    assert requirements == [second]
    assert links == [link]
    assert requirement_coverage(requirements, links) == (1, 1, 100)


def test_repository_persists_impact_and_workflow_transition(tmp_path) -> None:
    repository = SqliteGovernanceRepository(tmp_path / "governance.db")
    project_id = str(uuid4())
    impact = ImpactAssessment.assess(
        project_id=project_id,
        change_reference="change:shipment-activity",
        surface=ChangeSurface.API,
        assessed_by="System [local:test]",
    )
    repository.add_impact(impact)

    case = WorkflowCase.create(
        project_id=project_id,
        impact_assessment_id=impact.id,
        owner="Technical Writer",
        created_by="System [local:test]",
    )
    repository.add_workflow_case(case)
    updated = case.transition(WorkflowState.ANALYSIS)
    repository.update_workflow_case(
        updated,
        previous_state=case.state,
        actor="Technical Writer [local:test]",
        comment="Impact confirmed.",
    )

    persisted = repository.get_workflow_case(case.id)
    assert persisted is not None
    assert persisted.state is WorkflowState.ANALYSIS
