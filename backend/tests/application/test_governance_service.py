import asyncio

from tdp.identity.model import IdentityAssurance, RequestPrincipal
from tdp.modules.governance.application.service import GovernanceApplicationService
from tdp.modules.governance.domain.model import (
    ImpactAssessment,
    RequirementKind,
    RequirementRevision,
    TraceLink,
    TraceRelation,
    TraceTargetType,
    WorkflowAction,
    WorkflowEvent,
)
from tdp.modules.projects.domain.model import (
    Project,
    ProjectDescription,
    ProjectId,
    ProjectKey,
    ProjectName,
)
from tdp.modules.workspaces.domain.model import (
    Workspace,
    WorkspaceDescription,
    WorkspaceKey,
    WorkspaceName,
)


class InMemoryGovernanceRepository:
    def __init__(self) -> None:
        self.requirements: dict[str, RequirementRevision] = {}
        self.links: list[TraceLink] = []
        self.impacts: dict[str, ImpactAssessment] = {}
        self.events: list[WorkflowEvent] = []

    async def add_requirement(self, revision: RequirementRevision) -> None:
        self.requirements[revision.id] = revision

    async def add_revision(self, revision: RequirementRevision) -> None:
        self.requirements[revision.id] = revision

    async def get_requirement_revision(self, revision_id: str) -> RequirementRevision | None:
        return self.requirements.get(revision_id)

    async def get_latest_requirement(self, project_id: str, key: str) -> RequirementRevision | None:
        matches = [
            item
            for item in self.requirements.values()
            if item.project_id == project_id and item.key == key
        ]
        return max(matches, key=lambda item: item.revision) if matches else None

    async def list_latest_requirements(self, project_id: str) -> list[RequirementRevision]:
        latest: dict[str, RequirementRevision] = {}
        for item in self.requirements.values():
            if item.project_id != project_id:
                continue
            current = latest.get(item.key)
            if current is None or item.revision > current.revision:
                latest[item.key] = item
        return [latest[key] for key in sorted(latest)]

    async def add_trace_link(self, link: TraceLink) -> None:
        self.links.append(link)

    async def list_trace_links(self, project_id: str) -> list[TraceLink]:
        return [item for item in self.links if item.project_id == project_id]

    async def list_trace_links_for_target(
        self,
        project_id: str,
        target_type: str,
        target_id: str,
    ) -> list[TraceLink]:
        return [
            item
            for item in self.links
            if item.project_id == project_id
            and item.target_type.value == target_type
            and item.target_id == target_id
        ]

    async def add_impact_assessment(self, assessment: ImpactAssessment) -> None:
        self.impacts[assessment.id] = assessment

    async def update_impact_assessment(self, assessment: ImpactAssessment) -> None:
        self.impacts[assessment.id] = assessment

    async def get_impact_assessment(self, assessment_id: str) -> ImpactAssessment | None:
        return self.impacts.get(assessment_id)

    async def list_impact_assessments(self, project_id: str) -> list[ImpactAssessment]:
        return [item for item in self.impacts.values() if item.project_id == project_id]

    async def add_workflow_event(self, event: WorkflowEvent) -> None:
        self.events.append(event)

    async def list_workflow_events(self, assessment_id: str) -> list[WorkflowEvent]:
        return [item for item in self.events if item.assessment_id == assessment_id]


class InMemoryProjectRepository:
    def __init__(self, project: Project) -> None:
        self.project = project

    async def get(self, project_id: ProjectId) -> Project | None:
        return self.project if self.project.id == project_id else None


WORKSPACE = Workspace.create(
    key=WorkspaceKey("OPS"),
    name=WorkspaceName("Operations Workspace"),
    description=WorkspaceDescription("Operational products"),
)
PROJECT = Project.create(
    key=ProjectKey("DRIVER"),
    name=ProjectName("Driver Platform"),
    description=ProjectDescription("Driver operations"),
    workspace_id=str(WORKSPACE.id),
)
PRINCIPAL = RequestPrincipal(
    subject_id="writer-001",
    display_name="Technical Writer",
    email="writer@example.test",
    provider="local",
    assurance=IdentityAssurance.DEVELOPMENT,
)


def test_requirement_trace_impact_and_review_are_one_governed_chain() -> None:
    repository = InMemoryGovernanceRepository()
    service = GovernanceApplicationService(repository, InMemoryProjectRepository(PROJECT))

    requirement = asyncio.run(
        service.create_requirement(
            workspace_id=str(WORKSPACE.id),
            project_id=str(PROJECT.id),
            key="REQ-MEAL-001",
            kind=RequirementKind.FUNCTIONAL,
            title="Calculate meal allowance",
            statement="The system shall calculate meal allowance from the approved driver policy.",
            acceptance_criteria=("Calculation uses the active policy version.",),
            owner="Driver Product Owner",
            principal=PRINCIPAL,
        )
    )
    asyncio.run(
        service.add_trace_link(
            workspace_id=str(WORKSPACE.id),
            project_id=str(PROJECT.id),
            requirement_revision_id=requirement.id,
            target_type=TraceTargetType.FEATURE,
            target_id="meal-allowance",
            relation=TraceRelation.IMPLEMENTED_BY,
            rationale="Feature implements the requirement.",
            principal=PRINCIPAL,
        )
    )

    impact = asyncio.run(
        service.evaluate_impact(
            workspace_id=str(WORKSPACE.id),
            project_id=str(PROJECT.id),
            change_reference="commit:meal-v2",
            changed_target_type=TraceTargetType.FEATURE,
            changed_target_id="meal-allowance",
            principal=PRINCIPAL,
        )
    )
    submitted, submit_event = asyncio.run(
        service.transition_impact(
            workspace_id=str(WORKSPACE.id),
            project_id=str(PROJECT.id),
            assessment_id=impact.id,
            action=WorkflowAction.SUBMIT,
            comment="Ready for impact review.",
            principal=PRINCIPAL,
        )
    )
    approved, approve_event = asyncio.run(
        service.transition_impact(
            workspace_id=str(WORKSPACE.id),
            project_id=str(PROJECT.id),
            assessment_id=impact.id,
            action=WorkflowAction.APPROVE,
            comment="Impact reviewed against trace links.",
            principal=PRINCIPAL,
        )
    )

    assert impact.impacted_requirement_ids == (requirement.id,)
    assert "REVIEW_IMPLEMENTATION" in impact.required_actions
    assert submitted.workflow_state.value == "IN_REVIEW"
    assert approved.workflow_state.value == "APPROVED"
    assert submit_event.previous_state.value == "OPEN"
    assert approve_event.new_state.value == "APPROVED"


def test_requirement_revision_is_append_only() -> None:
    repository = InMemoryGovernanceRepository()
    service = GovernanceApplicationService(repository, InMemoryProjectRepository(PROJECT))

    first = asyncio.run(
        service.create_requirement(
            workspace_id=str(WORKSPACE.id),
            project_id=str(PROJECT.id),
            key="REQ-TRACK-001",
            kind=RequirementKind.BUSINESS,
            title="Track shipment activity",
            statement="Operations shall have an auditable view of shipment activity progression.",
            acceptance_criteria=(),
            owner="Operations",
            principal=PRINCIPAL,
        )
    )
    second = asyncio.run(
        service.revise_requirement(
            workspace_id=str(WORKSPACE.id),
            project_id=str(PROJECT.id),
            key=first.key,
            title="Track shipment activity and exceptions",
            statement="Operations shall have an auditable view of shipment activity and exceptions.",
            acceptance_criteria=("Exceptions are linked to their source evidence.",),
            owner="Operations",
            principal=PRINCIPAL,
        )
    )

    assert first.revision == 1
    assert second.revision == 2
    assert second.previous_revision_id == first.id
    assert len(repository.requirements) == 2
