from tdp.modules.catalog.domain.model import SynchronizationId, SynchronizationStatus
from tdp.modules.catalog.domain.repository import CatalogRepository
from tdp.modules.documents.domain.model import DocumentVersionId
from tdp.modules.documents.domain.repository import DocumentRepository
from tdp.modules.projects.domain.model import Project, ProjectId, ProjectStatus
from tdp.modules.projects.domain.repository import ProjectRepository
from tdp.modules.requirements.domain.model import RequirementId
from tdp.modules.requirements.domain.repository import RequirementRepository
from tdp.modules.workflow.domain.errors import (
    InvalidWorkflowEntityError,
    InvalidWorkflowPriorityError,
    InvalidWorkflowTransitionError,
    WorkflowEntityNotFoundError,
    WorkflowItemNotFoundError,
    WorkflowProjectArchivedError,
    WorkflowProjectNotFoundError,
    WorkflowWorkspaceMismatchError,
)
from tdp.modules.workflow.domain.model import (
    WorkflowAction,
    WorkflowEntityType,
    WorkflowEvent,
    WorkflowItem,
    WorkflowItemId,
    WorkflowPriority,
)
from tdp.modules.workflow.domain.repository import WorkflowRepository
from tdp.modules.workspaces.domain.model import WorkspaceId, WorkspaceStatus
from tdp.modules.workspaces.domain.repository import WorkspaceRepository


class WorkflowApplicationService:
    def __init__(
        self,
        repository: WorkflowRepository,
        project_repository: ProjectRepository,
        workspace_repository: WorkspaceRepository,
        requirement_repository: RequirementRepository,
        document_repository: DocumentRepository,
        catalog_repository: CatalogRepository,
    ) -> None:
        self._repository = repository
        self._project_repository = project_repository
        self._workspace_repository = workspace_repository
        self._requirement_repository = requirement_repository
        self._document_repository = document_repository
        self._catalog_repository = catalog_repository

    async def create(
        self,
        *,
        workspace_id: str,
        project_id: str,
        entity_type: str,
        entity_id: str,
        title: str,
        priority: str,
        assignee: str,
        actor: str,
    ) -> WorkflowItem:
        await self._require_project(workspace_id, project_id, writable=True)
        resolved_type = self._entity_type(entity_type)
        resolved_priority = self._priority(priority)
        await self._validate_entity(project_id, resolved_type, entity_id)
        item = WorkflowItem.create(
            workspace_id=workspace_id,
            project_id=project_id,
            entity_type=resolved_type,
            entity_id=entity_id,
            title=title,
            priority=resolved_priority,
            assignee=assignee,
            created_by=actor,
        )
        await self._repository.add(item)
        return item

    async def list_items(self, workspace_id: str, project_id: str) -> list[WorkflowItem]:
        await self._require_project(workspace_id, project_id, writable=False)
        return await self._repository.list_by_project(project_id)

    async def get(
        self,
        workspace_id: str,
        project_id: str,
        item_id: str,
    ) -> WorkflowItem:
        await self._require_project(workspace_id, project_id, writable=False)
        return await self._get_item(project_id, item_id)

    async def transition(
        self,
        *,
        workspace_id: str,
        project_id: str,
        item_id: str,
        action: str,
        comment: str,
        actor: str,
    ) -> WorkflowItem:
        await self._require_project(workspace_id, project_id, writable=True)
        item = await self._get_item(project_id, item_id)
        try:
            resolved_action = WorkflowAction(action.strip().upper())
        except ValueError as exc:
            raise InvalidWorkflowTransitionError(
                f"Workflow action {action} is not supported."
            ) from exc
        previous, new = item.transition(resolved_action)
        event = WorkflowEvent.create(
            workflow_item_id=item.id,
            action=resolved_action,
            previous_state=previous,
            new_state=new,
            actor=actor,
            comment=comment,
        )
        await self._repository.update(item, event)
        return item

    async def history(
        self,
        workspace_id: str,
        project_id: str,
        item_id: str,
    ) -> list[WorkflowEvent]:
        await self._require_project(workspace_id, project_id, writable=False)
        item = await self._get_item(project_id, item_id)
        return await self._repository.list_events(item.id)

    async def _validate_entity(
        self,
        project_id: str,
        entity_type: WorkflowEntityType,
        entity_id: str,
    ) -> None:
        if entity_type is WorkflowEntityType.REQUIREMENT:
            requirement = await self._requirement_repository.get(
                RequirementId.from_string(entity_id)
            )
            if requirement is None or requirement.project_id != project_id:
                raise WorkflowEntityNotFoundError(
                    f"Requirement {entity_id} was not found in project {project_id}."
                )
            return
        if entity_type is WorkflowEntityType.DOCUMENT:
            version = await self._document_repository.get_version(
                DocumentVersionId.from_string(entity_id)
            )
            if version is None or version.project_id != project_id:
                raise WorkflowEntityNotFoundError(
                    f"Document version {entity_id} was not found in project {project_id}."
                )
            return
        parts = entity_id.split("->", maxsplit=1)
        if len(parts) != 2:
            raise InvalidWorkflowEntityError(
                "CHANGE_IMPACT entity reference must use baseline_run_id->target_run_id."
            )
        baseline = await self._catalog_repository.get_run(
            SynchronizationId.from_string(parts[0])
        )
        target = await self._catalog_repository.get_run(
            SynchronizationId.from_string(parts[1])
        )
        if (
            baseline is None
            or target is None
            or baseline.project_id != project_id
            or target.project_id != project_id
            or baseline.status is not SynchronizationStatus.COMPLETED
            or target.status is not SynchronizationStatus.COMPLETED
        ):
            raise WorkflowEntityNotFoundError(
                "Change-impact workflow requires two completed project synchronization runs."
            )

    async def _get_item(self, project_id: str, item_id: str) -> WorkflowItem:
        item = await self._repository.get(WorkflowItemId.from_string(item_id))
        if item is None or item.project_id != project_id:
            raise WorkflowItemNotFoundError(
                f"Workflow item {item_id} was not found for project {project_id}."
            )
        return item

    async def _require_project(
        self,
        workspace_id: str,
        project_id: str,
        *,
        writable: bool,
    ) -> Project:
        project = await self._project_repository.get(ProjectId.from_string(project_id))
        if project is None:
            raise WorkflowProjectNotFoundError(f"Project {project_id} was not found.")
        if project.workspace_id != workspace_id:
            raise WorkflowWorkspaceMismatchError(
                f"Project {project_id} does not belong to workspace {workspace_id}."
            )
        workspace = await self._workspace_repository.get(WorkspaceId.from_string(workspace_id))
        if workspace is None:
            raise WorkflowWorkspaceMismatchError(
                f"Workspace {workspace_id} was not found for project {project_id}."
            )
        if writable and (
            project.status is ProjectStatus.ARCHIVED or workspace.status is WorkspaceStatus.ARCHIVED
        ):
            raise WorkflowProjectArchivedError(
                "Workflow items cannot be changed for an archived project or workspace."
            )
        return project

    @staticmethod
    def _entity_type(value: str) -> WorkflowEntityType:
        try:
            return WorkflowEntityType(value.strip().upper())
        except ValueError as exc:
            raise InvalidWorkflowEntityError(
                f"Workflow entity type {value} is not supported."
            ) from exc

    @staticmethod
    def _priority(value: str) -> WorkflowPriority:
        try:
            return WorkflowPriority(value.strip().upper())
        except ValueError as exc:
            raise InvalidWorkflowPriorityError(
                f"Workflow priority {value} is not supported."
            ) from exc
