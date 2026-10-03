from dataclasses import replace

from tdp.identity.model import RequestPrincipal
from tdp.modules.governance.domain.errors import (
    ImpactAssessmentNotFoundError,
    InvalidRequirementError,
    RequirementNotFoundError,
)
from tdp.modules.governance.domain.model import (
    ImpactAssessment,
    RequirementKind,
    RequirementRevision,
    RequirementStatus,
    TraceLink,
    TraceRelation,
    TraceTargetType,
    WorkflowAction,
    WorkflowEvent,
)
from tdp.modules.governance.domain.repository import GovernanceRepository
from tdp.modules.projects.domain.model import ProjectId
from tdp.modules.projects.domain.repository import ProjectRepository


class GovernanceApplicationService:
    def __init__(
        self,
        repository: GovernanceRepository,
        project_repository: ProjectRepository,
    ) -> None:
        self._repository = repository
        self._project_repository = project_repository

    async def create_requirement(
        self,
        *,
        workspace_id: str,
        project_id: str,
        key: str,
        kind: RequirementKind,
        title: str,
        statement: str,
        acceptance_criteria: tuple[str, ...],
        owner: str,
        principal: RequestPrincipal,
    ) -> RequirementRevision:
        await self._ensure_project(workspace_id, project_id)
        existing = await self._repository.get_latest_requirement(project_id, key.strip().upper())
        if existing is not None:
            raise InvalidRequirementError(
                f"Requirement key {key.strip().upper()} already exists; create a revision instead."
            )
        revision = RequirementRevision.create(
            workspace_id=workspace_id,
            project_id=project_id,
            key=key,
            kind=kind,
            title=title,
            statement=statement,
            acceptance_criteria=acceptance_criteria,
            owner=owner,
            created_by=principal.audit_actor,
        )
        await self._repository.add_requirement(revision)
        return revision

    async def revise_requirement(
        self,
        *,
        workspace_id: str,
        project_id: str,
        key: str,
        title: str,
        statement: str,
        acceptance_criteria: tuple[str, ...],
        owner: str,
        principal: RequestPrincipal,
    ) -> RequirementRevision:
        await self._ensure_project(workspace_id, project_id)
        latest = await self._repository.get_latest_requirement(project_id, key.strip().upper())
        if latest is None:
            raise RequirementNotFoundError(f"Requirement {key} was not found.")
        revision = RequirementRevision.create(
            workspace_id=workspace_id,
            project_id=project_id,
            key=latest.key,
            kind=latest.kind,
            title=title,
            statement=statement,
            acceptance_criteria=acceptance_criteria,
            owner=owner,
            created_by=principal.audit_actor,
            revision=latest.revision + 1,
            previous_revision_id=latest.id,
            status=RequirementStatus.DRAFT,
        )
        await self._repository.add_revision(revision)
        return revision

    async def list_requirements(
        self,
        workspace_id: str,
        project_id: str,
    ) -> list[RequirementRevision]:
        await self._ensure_project(workspace_id, project_id)
        return await self._repository.list_latest_requirements(project_id)

    async def add_trace_link(
        self,
        *,
        workspace_id: str,
        project_id: str,
        requirement_revision_id: str,
        target_type: TraceTargetType,
        target_id: str,
        relation: TraceRelation,
        rationale: str,
        principal: RequestPrincipal,
    ) -> TraceLink:
        await self._ensure_project(workspace_id, project_id)
        revision = await self._repository.get_requirement_revision(requirement_revision_id)
        if revision is None or revision.project_id != project_id:
            raise RequirementNotFoundError(
                f"Requirement revision {requirement_revision_id} was not found in the project."
            )
        link = TraceLink.create(
            workspace_id=workspace_id,
            project_id=project_id,
            requirement_revision_id=requirement_revision_id,
            target_type=target_type,
            target_id=target_id,
            relation=relation,
            rationale=rationale,
            created_by=principal.audit_actor,
        )
        await self._repository.add_trace_link(link)
        return link

    async def list_trace_links(
        self,
        workspace_id: str,
        project_id: str,
    ) -> list[TraceLink]:
        await self._ensure_project(workspace_id, project_id)
        return await self._repository.list_trace_links(project_id)

    async def evaluate_impact(
        self,
        *,
        workspace_id: str,
        project_id: str,
        change_reference: str,
        changed_target_type: TraceTargetType,
        changed_target_id: str,
        principal: RequestPrincipal,
    ) -> ImpactAssessment:
        await self._ensure_project(workspace_id, project_id)
        links = await self._repository.list_trace_links_for_target(
            project_id,
            changed_target_type.value,
            changed_target_id,
        )
        assessment = ImpactAssessment.evaluate(
            workspace_id=workspace_id,
            project_id=project_id,
            change_reference=change_reference,
            changed_target_type=changed_target_type,
            changed_target_id=changed_target_id,
            trace_links=tuple(links),
            created_by=principal.audit_actor,
        )
        await self._repository.add_impact_assessment(assessment)
        return assessment

    async def list_impacts(
        self,
        workspace_id: str,
        project_id: str,
    ) -> list[ImpactAssessment]:
        await self._ensure_project(workspace_id, project_id)
        return await self._repository.list_impact_assessments(project_id)

    async def transition_impact(
        self,
        *,
        workspace_id: str,
        project_id: str,
        assessment_id: str,
        action: WorkflowAction,
        comment: str,
        principal: RequestPrincipal,
    ) -> tuple[ImpactAssessment, WorkflowEvent]:
        await self._ensure_project(workspace_id, project_id)
        assessment = await self._repository.get_impact_assessment(assessment_id)
        if assessment is None or assessment.project_id != project_id:
            raise ImpactAssessmentNotFoundError(
                f"Impact assessment {assessment_id} was not found in the project."
            )
        previous_state = assessment.workflow_state
        transitioned = assessment.transition(action)
        event = WorkflowEvent.create(
            assessment_id=assessment.id,
            action=action,
            previous_state=previous_state,
            new_state=transitioned.workflow_state,
            actor=principal.audit_actor,
            comment=comment,
        )
        await self._repository.update_impact_assessment(transitioned)
        await self._repository.add_workflow_event(event)
        return transitioned, event

    async def list_workflow_events(
        self,
        *,
        workspace_id: str,
        project_id: str,
        assessment_id: str,
    ) -> list[WorkflowEvent]:
        await self._ensure_project(workspace_id, project_id)
        assessment = await self._repository.get_impact_assessment(assessment_id)
        if assessment is None or assessment.project_id != project_id:
            raise ImpactAssessmentNotFoundError(
                f"Impact assessment {assessment_id} was not found in the project."
            )
        return await self._repository.list_workflow_events(assessment_id)

    async def approve_requirement_revision(
        self,
        *,
        workspace_id: str,
        project_id: str,
        revision_id: str,
    ) -> RequirementRevision:
        await self._ensure_project(workspace_id, project_id)
        revision = await self._repository.get_requirement_revision(revision_id)
        if revision is None or revision.project_id != project_id:
            raise RequirementNotFoundError(f"Requirement revision {revision_id} was not found.")
        if revision.status is RequirementStatus.APPROVED:
            return revision
        approved = replace(revision, status=RequirementStatus.APPROVED)
        # Requirement revisions are immutable facts. Approval is intentionally not persisted
        # until a dedicated approval event store is introduced; callers should use impact
        # workflow for governed decisions in the current enterprise core slice.
        return approved

    async def _ensure_project(self, workspace_id: str, project_id: str) -> None:
        try:
            parsed_id = ProjectId.from_string(project_id)
        except Exception as exc:
            raise InvalidRequirementError("Project reference must be a valid UUID.") from exc
        project = await self._project_repository.get(parsed_id)
        if project is None or project.workspace_id != workspace_id:
            raise RequirementNotFoundError(
                f"Project {project_id} was not found in workspace {workspace_id}."
            )
