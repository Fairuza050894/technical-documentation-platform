from dataclasses import dataclass

from tdp.modules.documents.domain.governance import (
    DOCUMENT_TYPE_REGISTRY_SCHEMA_VERSION,
    PROJECT_DOCUMENTATION_POLICY_KEY,
    DocumentTypeDefinition,
    ProjectDocumentAvailability,
    ProjectDocumentRequirement,
)


@dataclass(frozen=True, slots=True)
class DocumentTypeDefinitionDto:
    document_type: str
    display_name: str
    description: str
    automation_profile: str
    order: int

    @classmethod
    def from_domain(cls, item: DocumentTypeDefinition) -> "DocumentTypeDefinitionDto":
        return cls(
            document_type=item.document_type.value,
            display_name=item.display_name,
            description=item.description,
            automation_profile=item.automation_profile.value,
            order=item.order,
        )


@dataclass(frozen=True, slots=True)
class DocumentTypeRegistryDto:
    schema_version: str
    items: list[DocumentTypeDefinitionDto]
    total: int


@dataclass(frozen=True, slots=True)
class ProjectDocumentationChecklistItemDto:
    document_type: str
    display_name: str
    automation_profile: str
    requirement: str
    availability: str
    latest_document_id: str | None
    latest_version_id: str | None
    latest_version: str | None
    latest_status: str | None


@dataclass(frozen=True, slots=True)
class ProjectDocumentationChecklistDto:
    project_id: str
    policy_key: str
    registry_schema_version: str
    items: list[ProjectDocumentationChecklistItemDto]
    total: int
    required_total: int
    supplementary_total: int
    available_total: int
    missing_required_total: int

    @classmethod
    def create(
        cls,
        *,
        project_id: str,
        items: list[ProjectDocumentationChecklistItemDto],
    ) -> "ProjectDocumentationChecklistDto":
        required_total = sum(
            item.requirement == ProjectDocumentRequirement.REQUIRED.value for item in items
        )
        supplementary_total = sum(
            item.requirement == ProjectDocumentRequirement.SUPPLEMENTARY.value for item in items
        )
        available_total = sum(
            item.availability == ProjectDocumentAvailability.AVAILABLE.value for item in items
        )
        missing_required_total = sum(
            item.requirement == ProjectDocumentRequirement.REQUIRED.value
            and item.availability == ProjectDocumentAvailability.MISSING.value
            for item in items
        )
        return cls(
            project_id=project_id,
            policy_key=PROJECT_DOCUMENTATION_POLICY_KEY,
            registry_schema_version=DOCUMENT_TYPE_REGISTRY_SCHEMA_VERSION,
            items=items,
            total=len(items),
            required_total=required_total,
            supplementary_total=supplementary_total,
            available_total=available_total,
            missing_required_total=missing_required_total,
        )
