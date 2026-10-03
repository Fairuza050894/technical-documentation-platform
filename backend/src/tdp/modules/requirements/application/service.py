from tdp.modules.documents.domain.model import DocumentVersionId
from tdp.modules.documents.domain.repository import DocumentRepository
from tdp.modules.evidence.domain.model import EvidenceArtifactId
from tdp.modules.evidence.domain.repository import EvidenceRepository
from tdp.modules.features.domain.model import FeatureId
from tdp.modules.features.domain.repository import FeatureRepository
from tdp.modules.projects.domain.model import Project, ProjectId, ProjectStatus
from tdp.modules.projects.domain.repository import ProjectRepository
from tdp.modules.requirements.domain.errors import (
    InvalidRequirementStatusTransitionError,
    InvalidRequirementTypeError,
    InvalidTraceabilityTargetError,
    RequirementFeatureNotFoundError,
    RequirementKeyAlreadyExistsError,
    RequirementNotFoundError,
    RequirementProjectArchivedError,
    RequirementProjectNotFoundError,
    RequirementWorkspaceMismatchError,
    TraceabilityTargetNotFoundError,
)
from tdp.modules.requirements.domain.model import (
    Requirement,
    RequirementId,
    RequirementRevision,
    RequirementStatus,
    RequirementType,
    TraceabilityLink,
    TraceabilityRelation,
    TraceabilityTargetType,
)
from tdp.modules.requirements.domain.repository import RequirementRepository
from tdp.modules.workspaces.domain.model import WorkspaceId, WorkspaceStatus
from tdp.modules.workspaces.domain.repository import WorkspaceRepository

_EXPECTED_RELATION: dict[TraceabilityTargetType, TraceabilityRelation] = {
    TraceabilityTargetType.FEATURE: TraceabilityRelation.IMPLEMENTED_BY,
    TraceabilityTargetType.EVIDENCE: TraceabilityRelation.SUPPORTED_BY,
    TraceabilityTargetType.DOCUMENT: TraceabilityRelation.DOCUMENTED_BY,
    TraceabilityTargetType.TEST: TraceabilityRelation.VERIFIED_BY,
    TraceabilityTargetType.CHANGE: TraceabilityRelation.AFFECTED_BY,
}


class RequirementApplicationService:
    def __init__(
        self,
        repository: RequirementRepository,
        project_repository: ProjectRepository,
        workspace_repository: WorkspaceRepository,
        feature_repository: FeatureRepository,
        evidence_repository: EvidenceRepository,
        document_repository: DocumentRepository,
    ) -> None:
        self._repository = repository
        self._project_repository = project_repository
        self._workspace_repository = workspace_repository
        self._feature_repository = feature_repository
        self._evidence_repository = evidence_repository
        self._document_repository = document_repository

    async def create(
        self,
        *,
        workspace_id: str,
        project_id: str,
        key: str,
        requirement_type: str,
        title: str,
        statement: str,
        acceptance_criteria: tuple[str, ...],
        rationale: str,
        feature_id: str | None,
        actor: str,
    ) -> Requirement:
        await self._require_project(workspace_id, project_id, writable=True)
        normalized_key = key.strip().upper()
        if await self._repository.get_by_project_key(project_id, normalized_key) is not None:
            raise RequirementKeyAlreadyExistsError(
                f"Requirement key {normalized_key} is already in use inside project {project_id}."
            )
        resolved_type = self._requirement_type(requirement_type)
        await self._validate_feature(project_id, feature_id)
        requirement = Requirement.create(
            workspace_id=workspace_id,
            project_id=project_id,
            key=normalized_key,
            requirement_type=resolved_type,
            title=title,
            statement=statement,
            acceptance_criteria=acceptance_criteria,
            rationale=rationale,
            feature_id=feature_id,
            created_by=actor,
        )
        await self._repository.add(
            requirement,
            RequirementRevision.from_requirement(requirement, actor=actor),
        )
        return requirement

    async def list_requirements(
        self,
        workspace_id: str,
        project_id: str,
    ) -> list[Requirement]:
        await self._require_project(workspace_id, project_id, writable=False)
        return await self._repository.list_by_project(project_id)

    async def get(
        self,
        workspace_id: str,
        project_id: str,
        requirement_id: str,
    ) -> Requirement:
        await self._require_project(workspace_id, project_id, writable=False)
        return await self._get_requirement(project_id, requirement_id)

    async def revise(
        self,
        *,
        workspace_id: str,
        project_id: str,
        requirement_id: str,
        title: str,
        statement: str,
        acceptance_criteria: tuple[str, ...],
        rationale: str,
        feature_id: str | None,
        actor: str,
    ) -> Requirement:
        await self._require_project(workspace_id, project_id, writable=True)
        requirement = await self._get_requirement(project_id, requirement_id)
        await self._validate_feature(project_id, feature_id)
        requirement.revise(
            title=title,
            statement=statement,
            acceptance_criteria=acceptance_criteria,
            rationale=rationale,
            feature_id=feature_id,
        )
        await self._repository.update(
            requirement,
            RequirementRevision.from_requirement(requirement, actor=actor),
        )
        return requirement

    async def transition(
        self,
        *,
        workspace_id: str,
        project_id: str,
        requirement_id: str,
        action: str,
        actor: str,
    ) -> Requirement:
        await self._require_project(workspace_id, project_id, writable=True)
        requirement = await self._get_requirement(project_id, requirement_id)
        normalized_action = action.strip().upper()
        if normalized_action == "APPROVE":
            requirement.approve()
        elif normalized_action == "RETIRE":
            requirement.retire()
        else:
            raise InvalidRequirementStatusTransitionError(
                "Requirement action must be APPROVE or RETIRE."
            )
        await self._repository.update(
            requirement,
            RequirementRevision.from_requirement(requirement, actor=actor),
        )
        return requirement

    async def history(
        self,
        workspace_id: str,
        project_id: str,
        requirement_id: str,
    ) -> list[RequirementRevision]:
        await self._require_project(workspace_id, project_id, writable=False)
        requirement = await self._get_requirement(project_id, requirement_id)
        return await self._repository.list_revisions(requirement.id)

    async def add_traceability_link(
        self,
        *,
        workspace_id: str,
        project_id: str,
        requirement_id: str,
        target_type: str,
        target_id: str,
        relation: str,
        actor: str,
    ) -> TraceabilityLink:
        await self._require_project(workspace_id, project_id, writable=True)
        requirement = await self._get_requirement(project_id, requirement_id)
        try:
            resolved_target_type = TraceabilityTargetType(target_type.strip().upper())
            resolved_relation = TraceabilityRelation(relation.strip().upper())
        except ValueError as exc:
            raise InvalidTraceabilityTargetError(
                "Unsupported traceability target type or relation."
            ) from exc
        expected = _EXPECTED_RELATION[resolved_target_type]
        if resolved_relation is not expected:
            raise InvalidTraceabilityTargetError(
                f"{resolved_target_type.value} targets require {expected.value} relation."
            )
        await self._validate_target(
            project_id=project_id,
            target_type=resolved_target_type,
            target_id=target_id,
        )
        link = TraceabilityLink.create(
            requirement_id=requirement.id,
            target_type=resolved_target_type,
            target_id=target_id,
            relation=resolved_relation,
            created_by=actor,
        )
        await self._repository.add_link(link)
        return link

    async def traceability(
        self,
        workspace_id: str,
        project_id: str,
        requirement_id: str,
    ) -> list[TraceabilityLink]:
        await self._require_project(workspace_id, project_id, writable=False)
        requirement = await self._get_requirement(project_id, requirement_id)
        return await self._repository.list_links(requirement.id)

    async def project_traceability(
        self,
        workspace_id: str,
        project_id: str,
    ) -> list[tuple[Requirement, list[TraceabilityLink]]]:
        await self._require_project(workspace_id, project_id, writable=False)
        requirements = await self._repository.list_by_project(project_id)
        return [
            (requirement, await self._repository.list_links(requirement.id))
            for requirement in requirements
        ]

    async def _validate_target(
        self,
        *,
        project_id: str,
        target_type: TraceabilityTargetType,
        target_id: str,
    ) -> None:
        if target_type is TraceabilityTargetType.FEATURE:
            feature = await self._feature_repository.get(FeatureId.from_string(target_id))
            if feature is None or feature.project_id != project_id:
                raise TraceabilityTargetNotFoundError(
                    f"Feature {target_id} was not found in project {project_id}."
                )
            return
        if target_type is TraceabilityTargetType.EVIDENCE:
            artifact = await self._evidence_repository.get_artifact(
                EvidenceArtifactId.from_string(target_id)
            )
            if artifact is None or artifact.project_id != project_id:
                raise TraceabilityTargetNotFoundError(
                    f"Evidence {target_id} was not found in project {project_id}."
                )
            return
        if target_type is TraceabilityTargetType.DOCUMENT:
            version = await self._document_repository.get_version(
                DocumentVersionId.from_string(target_id)
            )
            if version is None or version.project_id != project_id:
                raise TraceabilityTargetNotFoundError(
                    f"Document version {target_id} was not found in project {project_id}."
                )
            return
        normalized = target_id.strip()
        if not normalized or len(normalized) > 500:
            raise InvalidTraceabilityTargetError(
                "External traceability targets must contain 1-500 characters."
            )

    async def _validate_feature(self, project_id: str, feature_id: str | None) -> None:
        if feature_id is None:
            return
        feature = await self._feature_repository.get(FeatureId.from_string(feature_id))
        if feature is None or feature.project_id != project_id:
            raise RequirementFeatureNotFoundError(
                f"Feature {feature_id} was not found in project {project_id}."
            )

    async def _get_requirement(self, project_id: str, requirement_id: str) -> Requirement:
        requirement = await self._repository.get(RequirementId.from_string(requirement_id))
        if requirement is None or requirement.project_id != project_id:
            raise RequirementNotFoundError(
                f"Requirement {requirement_id} was not found for project {project_id}."
            )
        return requirement

    async def _require_project(
        self,
        workspace_id: str,
        project_id: str,
        *,
        writable: bool,
    ) -> Project:
        project = await self._project_repository.get(ProjectId.from_string(project_id))
        if project is None:
            raise RequirementProjectNotFoundError(f"Project {project_id} was not found.")
        if project.workspace_id != workspace_id:
            raise RequirementWorkspaceMismatchError(
                f"Project {project_id} does not belong to workspace {workspace_id}."
            )
        workspace = await self._workspace_repository.get(WorkspaceId.from_string(workspace_id))
        if workspace is None:
            raise RequirementWorkspaceMismatchError(
                f"Workspace {workspace_id} was not found for project {project_id}."
            )
        if writable and (
            project.status is ProjectStatus.ARCHIVED or workspace.status is WorkspaceStatus.ARCHIVED
        ):
            raise RequirementProjectArchivedError(
                "Requirements cannot be changed for an archived project or workspace."
            )
        return project

    @staticmethod
    def _requirement_type(value: str) -> RequirementType:
        try:
            return RequirementType(value.strip().upper())
        except ValueError as exc:
            raise InvalidRequirementTypeError(
                f"Requirement type {value} is not supported."
            ) from exc

    @staticmethod
    def is_approved(requirement: Requirement) -> bool:
        return requirement.status is RequirementStatus.APPROVED
