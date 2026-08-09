from datetime import datetime

from tdp.modules.documents.application.governance_dto import (
    DocumentTypeDefinitionDto,
    DocumentTypeRegistryDto,
    ProjectDocumentationChecklistDto,
    ProjectDocumentationChecklistItemDto,
)
from tdp.modules.documents.domain.errors import DocumentProjectNotFoundError
from tdp.modules.documents.domain.governance import (
    DOCUMENT_TYPE_REGISTRY,
    DOCUMENT_TYPE_REGISTRY_SCHEMA_VERSION,
    PROJECT_DOCUMENTATION_POLICY,
    ProjectDocumentAvailability,
    document_type_definition,
)
from tdp.modules.documents.domain.model import DocumentType, DocumentVersion
from tdp.modules.documents.domain.repository import DocumentRepository
from tdp.modules.projects.domain.model import ProjectId
from tdp.modules.projects.domain.repository import ProjectRepository


class DocumentGovernanceApplicationService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        project_repository: ProjectRepository,
    ) -> None:
        self._document_repository = document_repository
        self._project_repository = project_repository

    async def list_document_types(self) -> DocumentTypeRegistryDto:
        items = [DocumentTypeDefinitionDto.from_domain(item) for item in DOCUMENT_TYPE_REGISTRY]
        return DocumentTypeRegistryDto(
            schema_version=DOCUMENT_TYPE_REGISTRY_SCHEMA_VERSION,
            items=items,
            total=len(items),
        )

    async def project_documentation_checklist(
        self,
        project_id: str,
    ) -> ProjectDocumentationChecklistDto:
        project = await self._project_repository.get(ProjectId.from_string(project_id))
        if project is None:
            raise DocumentProjectNotFoundError(f"Project {project_id} was not found.")

        versions = await self._document_repository.list_versions_by_project(project_id)
        latest_by_type = self._latest_governed_versions(versions)

        items: list[ProjectDocumentationChecklistItemDto] = []
        for policy_item in PROJECT_DOCUMENTATION_POLICY:
            definition = document_type_definition(policy_item.document_type)
            version = latest_by_type.get(policy_item.document_type)
            items.append(
                ProjectDocumentationChecklistItemDto(
                    document_type=policy_item.document_type.value,
                    display_name=definition.display_name,
                    automation_profile=definition.automation_profile.value,
                    requirement=policy_item.requirement.value,
                    availability=(
                        ProjectDocumentAvailability.AVAILABLE.value
                        if version is not None
                        else ProjectDocumentAvailability.MISSING.value
                    ),
                    latest_document_id=(str(version.document_id) if version is not None else None),
                    latest_version_id=(str(version.id) if version is not None else None),
                    latest_version=(str(version.version_number) if version is not None else None),
                    latest_status=(version.status.value if version is not None else None),
                )
            )

        return ProjectDocumentationChecklistDto.create(
            project_id=str(project.id),
            items=items,
        )

    @staticmethod
    def _latest_governed_versions(
        versions: list[DocumentVersion],
    ) -> dict[DocumentType, DocumentVersion]:
        governed_types = {item.document_type for item in DOCUMENT_TYPE_REGISTRY}
        latest_by_type: dict[DocumentType, DocumentVersion] = {}

        for version in versions:
            if version.document_type not in governed_types:
                continue
            current = latest_by_type.get(version.document_type)
            if current is None or _version_sort_key(version) > _version_sort_key(current):
                latest_by_type[version.document_type] = version

        return latest_by_type


def _version_sort_key(version: DocumentVersion) -> tuple[datetime, int, int, str]:
    return (
        version.created_at,
        version.version_number.major,
        version.version_number.minor,
        str(version.id),
    )
