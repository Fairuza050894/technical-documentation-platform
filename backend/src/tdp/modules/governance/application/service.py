import sqlite3
from dataclasses import asdict

from tdp.modules.governance.domain.model import (
    ChangeSurface,
    ImpactAssessment,
    RequirementRevision,
    RequirementStatus,
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
from tdp.modules.projects.application.service import ProjectApplicationService


class GovernanceApplicationService:
    def __init__(
        self,
        repository: SqliteGovernanceRepository,
        project_service: ProjectApplicationService,
    ) -> None:
        self._repository = repository
        self._project_service = project_service

    async def create_requirement(
        self,
        *,
        project_id: str,
        requirement_type: RequirementType,
        title: str,
        statement: str,
        rationale: str,
        actor: str,
    ) -> RequirementRevision:
        await self._project_service.get(project_id)
        revision = RequirementRevision.create(
            project_id=project_id,
            requirement_type=requirement_type,
            title=title,
            statement=statement,
            rationale=rationale,
            created_by=actor,
        )
        self._repository.add_requirement(revision)
        return revision

    async def create_requirement_revision(
        self,
        *,
        requirement_id: str,
        title: str,
        statement: str,
        rationale: str,
        actor: str,
        status: RequirementStatus | None = None,
    ) -> RequirementRevision:
        current = self._repository.latest_requirement(requirement_id)
        if current is None:
            raise LookupError(f"Requirement {requirement_id} was not found.")
        await self._project_service.get(current.project_id)
        revision = RequirementRevision.create(
            project_id=current.project_id,
            requirement_id=current.requirement_id,
            revision=current.revision + 1,
            requirement_type=current.requirement_type,
            status=status or current.status,
            title=title,
            statement=statement,
            rationale=rationale,
            created_by=actor,
        )
        self._repository.add_requirement(revision)
        return revision

    async def list_requirements(self, project_id: str) -> list[RequirementRevision]:
        await self._project_service.get(project_id)
        return self._repository.list_requirements(project_id)

    async def create_trace_link(
        self,
        *,
        project_id: str,
        requirement_id: str,
        target_type: TraceTargetType,
        target_id: str,
        relation: str,
        actor: str,
    ) -> TraceLink:
        await self._project_service.get(project_id)
        requirement = self._repository.latest_requirement(requirement_id)
        if requirement is None or requirement.project_id != project_id:
            raise LookupError(f"Requirement {requirement_id} was not found in project {project_id}.")
        link = TraceLink.create(
            project_id=project_id,
            requirement_id=requirement_id,
            target_type=target_type,
            target_id=target_id,
            relation=relation,
            created_by=actor,
        )
        try:
            self._repository.add_trace_link(link)
        except sqlite3.IntegrityError as exc:
            raise ValueError("An identical trace link already exists.") from exc
        return link

    async def traceability_summary(self, project_id: str) -> dict[str, object]:
        requirements = await self.list_requirements(project_id)
        links = self._repository.list_trace_links(project_id)
        total, linked, coverage = requirement_coverage(requirements, links)
        by_target: dict[str, int] = {}
        for link in links:
            by_target[link.target_type.value] = by_target.get(link.target_type.value, 0) + 1
        return {
            "requirements": [asdict(item) for item in requirements],
            "trace_links": [asdict(item) for item in links],
            "requirement_total": total,
            "linked_requirement_total": linked,
            "coverage_percent": coverage,
            "links_by_target": by_target,
        }

    async def assess_impact(
        self,
        *,
        project_id: str,
        change_reference: str,
        surface: ChangeSurface,
        actor: str,
    ) -> ImpactAssessment:
        await self._project_service.get(project_id)
        assessment = ImpactAssessment.assess(
            project_id=project_id,
            change_reference=change_reference,
            surface=surface,
            assessed_by=actor,
        )
        self._repository.add_impact(assessment)
        return assessment

    async def create_workflow_case(
        self,
        *,
        project_id: str,
        impact_assessment_id: str,
        owner: str,
        actor: str,
    ) -> WorkflowCase:
        await self._project_service.get(project_id)
        impact = self._repository.get_impact(impact_assessment_id)
        if impact is None or impact.project_id != project_id:
            raise LookupError(
                f"Impact assessment {impact_assessment_id} was not found in project {project_id}."
            )
        if any(
            item.impact_assessment_id == impact_assessment_id
            for item in self._repository.list_workflow_cases(project_id)
        ):
            raise ValueError(
                f"A workflow case already exists for impact assessment {impact_assessment_id}."
            )
        case = WorkflowCase.create(
            project_id=project_id,
            impact_assessment_id=impact_assessment_id,
            owner=owner,
            created_by=actor,
        )
        self._repository.add_workflow_case(case)
        return case

    async def transition_workflow_case(
        self,
        *,
        case_id: str,
        target: WorkflowState,
        actor: str,
        comment: str,
    ) -> WorkflowCase:
        case = self._repository.get_workflow_case(case_id)
        if case is None:
            raise LookupError(f"Workflow case {case_id} was not found.")
        previous_state = case.state
        updated = case.transition(target)
        self._repository.update_workflow_case(
            updated,
            previous_state=previous_state,
            actor=actor,
            comment=" ".join(comment.split())[:500],
        )
        return updated

    async def governance_summary(self, project_id: str) -> dict[str, object]:
        traceability = await self.traceability_summary(project_id)
        impacts = self._repository.list_impacts(project_id)
        workflow_cases = self._repository.list_workflow_cases(project_id)
        open_states = {
            WorkflowState.OPEN,
            WorkflowState.ANALYSIS,
            WorkflowState.UPDATE_REQUIRED,
            WorkflowState.IN_REVIEW,
        }
        return {
            **traceability,
            "impact_assessments": [asdict(item) for item in impacts],
            "workflow_cases": [asdict(item) for item in workflow_cases],
            "impact_total": len(impacts),
            "open_workflow_total": sum(1 for item in workflow_cases if item.state in open_states),
        }
