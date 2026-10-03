from tdp.modules.documents.domain.model import DocumentId
from tdp.modules.documents.domain.repository import DocumentRepository
from tdp.modules.evidence.domain.model import EvidenceArtifactId
from tdp.modules.evidence.domain.repository import EvidenceRepository
from tdp.modules.features.domain.model import FeatureId
from tdp.modules.features.domain.repository import FeatureRepository
from tdp.modules.projects.domain.model import Project, ProjectId, ProjectStatus
from tdp.modules.projects.domain.repository import ProjectRepository
from tdp.modules.requirements.application.commands import (
    CreateRequirementCommand,
    CreateTraceLinkCommand,
    RetireRequirementCommand,
    ReviseRequirementCommand,
)
from tdp.modules.requirements.application.dto import RequirementDto, TraceabilityCoverageDto
from tdp.modules.requirements.domain.errors import (
    InvalidRequirementTypeError,
    RequirementKeyAlreadyExistsError,
    RequirementNotFoundError,
    RequirementProjectArchivedError,
    RequirementProjectNotFoundError,
    RequirementWorkspaceMismatchError,
    TraceTargetNotFoundError,
)
from tdp.modules.requirements.domain.model import (
    RequirementId,
    RequirementKey,
    RequirementRevision,
    RequirementType,
    TraceLink,
    TraceRelation,
    TraceTargetType,
)
from tdp.modules.requirements.domain.repository import RequirementRepository
from tdp.modules.workspaces.domain.model import WorkspaceId, WorkspaceStatus
from tdp.modules.workspaces.domain.repository import WorkspaceRepository


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

    async def create(self, command: CreateRequirementCommand) -> RequirementDto:
        await self._require_project(command.workspace_id, command.project_id, writable=True)
        key = RequirementKey(command.key)
        if await self._repository.get_latest_by_key(command.project_id, key) is not None:
            raise RequirementKeyAlreadyExistsError(
                f"Requirement key {key} is already in use inside project {command.project_id}."
            )
        requirement_type = self._requirement_type(command.requirement_type)
        await self._validate_feature(command.project_id, command.feature_id)
        revision = RequirementRevision.create(
            project_id=command.project_id,
            key=command.key,
            requirement_type=requirement_type,
            title=command.title,
            statement=command.statement,
            owner=command.owner,
            feature_id=command.feature_id,
            acceptance_criteria=command.acceptance_criteria,
            changed_by=command.actor,
            change_reason=command.change_reason,
        )
        feature_links = self._feature_trace_links(revision, command.actor)
        await self._repository.add_revision(revision, feature_links)
        return RequirementDto.from_domain(revision, list(feature_links))

    async def list_requirements(
        self,
        workspace_id: str,
        project_id: str,
    ) -> list[RequirementDto]:
        await self._require_project(workspace_id, project_id, writable=False)
        revisions = await self._repository.list_latest_by_project(project_id)
        return [await self._to_dto(revision) for revision in revisions]

    async def get(
        self,
        workspace_id: str,
        project_id: str,
        requirement_id: str,
    ) -> RequirementDto:
        await self._require_project(workspace_id, project_id, writable=False)
        revision = await self._require_latest(project_id, requirement_id)
        return await self._to_dto(revision)

    async def list_revisions(
        self,
        workspace_id: str,
        project_id: str,
        requirement_id: str,
    ) -> list[RequirementDto]:
        await self._require_project(workspace_id, project_id, writable=False)
        parsed_id = RequirementId.from_string(requirement_id)
        revisions = await self._repository.list_revisions(project_id, parsed_id)
        if not revisions:
            raise RequirementNotFoundError(
                f"Requirement {requirement_id} was not found for project {project_id}."
            )
        return [await self._to_dto(revision) for revision in revisions]

    async def revise(self, command: ReviseRequirementCommand) -> RequirementDto:
        await self._require_project(command.workspace_id, command.project_id, writable=True)
        current = await self._require_latest(command.project_id, command.requirement_id)
        await self._validate_feature(command.project_id, command.feature_id)
        revision = current.revise(
            requirement_type=self._requirement_type(command.requirement_type),
            title=command.title,
            statement=command.statement,
            owner=command.owner,
            feature_id=command.feature_id,
            acceptance_criteria=command.acceptance_criteria,
            changed_by=command.actor,
            change_reason=command.change_reason,
        )
        feature_links = self._feature_trace_links(revision, command.actor)
        await self._repository.add_revision(revision, feature_links)
        return RequirementDto.from_domain(revision, list(feature_links))

    async def retire(self, command: RetireRequirementCommand) -> RequirementDto:
        await self._require_project(command.workspace_id, command.project_id, writable=True)
        current = await self._require_latest(command.project_id, command.requirement_id)
        revision = current.retire(
            changed_by=command.actor,
            change_reason=command.change_reason,
        )
        await self._repository.add_revision(revision)
        return RequirementDto.from_domain(revision, [])

    async def add_trace_link(self, command: CreateTraceLinkCommand) -> RequirementDto:
        await self._require_project(command.workspace_id, command.project_id, writable=True)
        current = await self._require_latest(command.project_id, command.requirement_id)
        try:
            target_type = TraceTargetType(command.target_type)
            relation = TraceRelation(command.relation)
        except ValueError as exc:
            raise InvalidRequirementTypeError("Unsupported trace target or relation.") from exc

        await self._verify_trace_target(
            command.project_id,
            target_type,
            command.target_reference,
        )
        link = TraceLink.create(
            project_id=command.project_id,
            requirement_revision_id=current.revision_id,
            target_type=target_type,
            relation=relation,
            target_reference=command.target_reference,
            verified=True,
            created_by=command.actor,
        )
        await self._repository.add_trace_link(link)
        return await self._to_dto(current)

    async def coverage(
        self,
        workspace_id: str,
        project_id: str,
    ) -> TraceabilityCoverageDto:
        await self._require_project(workspace_id, project_id, writable=False)
        revisions = [
            revision
            for revision in await self._repository.list_latest_by_project(project_id)
            if revision.status.value == "ACTIVE"
        ]
        feature_count = 0
        evidence_count = 0
        document_count = 0
        fully_traced = 0
        for revision in revisions:
            links = await self._repository.list_trace_links(revision.revision_id)
            types = {link.target_type for link in links if link.verified}
            if TraceTargetType.FEATURE in types:
                feature_count += 1
            if TraceTargetType.EVIDENCE in types:
                evidence_count += 1
            if TraceTargetType.DOCUMENT in types:
                document_count += 1
            if {
                TraceTargetType.FEATURE,
                TraceTargetType.EVIDENCE,
                TraceTargetType.DOCUMENT,
            }.issubset(types):
                fully_traced += 1
        return TraceabilityCoverageDto(
            total_requirements=len(revisions),
            linked_to_feature=feature_count,
            linked_to_evidence=evidence_count,
            linked_to_document=document_count,
            fully_traced=fully_traced,
        )

    async def _to_dto(self, revision: RequirementRevision) -> RequirementDto:
        links = await self._repository.list_trace_links(revision.revision_id)
        return RequirementDto.from_domain(revision, links)

    async def _require_latest(
        self,
        project_id: str,
        requirement_id: str,
    ) -> RequirementRevision:
        revision = await self._repository.get_latest(
            project_id,
            RequirementId.from_string(requirement_id),
        )
        if revision is None:
            raise RequirementNotFoundError(
                f"Requirement {requirement_id} was not found for project {project_id}."
            )
        return revision

    async def _validate_feature(self, project_id: str, feature_id: str | None) -> None:
        if feature_id is None:
            return
        feature = await self._feature_repository.get(FeatureId.from_string(feature_id))
        if feature is None or feature.project_id != project_id:
            raise TraceTargetNotFoundError(
                f"Feature {feature_id} was not found for project {project_id}."
            )

    @staticmethod
    def _feature_trace_links(
        revision: RequirementRevision,
        actor: str,
    ) -> tuple[TraceLink, ...]:
        if revision.feature_id is None:
            return ()
        return (
            TraceLink.create(
                project_id=revision.project_id,
                requirement_revision_id=revision.revision_id,
                target_type=TraceTargetType.FEATURE,
                relation=TraceRelation.IMPLEMENTED_BY,
                target_reference=revision.feature_id,
                verified=True,
                created_by=actor,
            ),
        )

    async def _verify_trace_target(
        self,
        project_id: str,
        target_type: TraceTargetType,
        target_reference: str,
    ) -> None:
        if target_type is TraceTargetType.FEATURE:
            feature = await self._feature_repository.get(FeatureId.from_string(target_reference))
            if feature is None or feature.project_id != project_id:
                raise TraceTargetNotFoundError(
                    f"Feature {target_reference} was not found for project {project_id}."
                )
            return
        if target_type is TraceTargetType.EVIDENCE:
            artifact = await self._evidence_repository.get_artifact(
                EvidenceArtifactId.from_string(target_reference)
            )
            if artifact is None or artifact.project_id != project_id:
                raise TraceTargetNotFoundError(
                    f"Evidence {target_reference} was not found for project {project_id}."
                )
            return
        series = await self._document_repository.get_series(
            DocumentId.from_string(target_reference)
        )
        if series is None or series.project_id != project_id:
            raise TraceTargetNotFoundError(
                f"Document {target_reference} was not found for project {project_id}."
            )

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
            return RequirementType(value)
        except ValueError as exc:
            raise InvalidRequirementTypeError(
                f"Requirement type {value} is not supported."
            ) from exc
