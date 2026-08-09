import asyncio
from datetime import UTC, datetime, timedelta

from tdp.modules.documents.application.governance_service import (
    DocumentGovernanceApplicationService,
)
from tdp.modules.documents.domain.model import (
    DocumentId,
    DocumentType,
    DocumentVersion,
    DocumentVersionNumber,
)
from tdp.modules.projects.domain.model import (
    Project,
    ProjectDescription,
    ProjectKey,
    ProjectName,
)


class ProjectRepositoryStub:
    def __init__(self, project: Project | None) -> None:
        self.project = project

    async def get(self, _project_id: object) -> Project | None:
        return self.project


class DocumentRepositoryStub:
    def __init__(self, versions: list[DocumentVersion]) -> None:
        self.versions = versions

    async def list_versions_by_project(self, _project_id: str) -> list[DocumentVersion]:
        return self.versions


def _project() -> Project:
    return Project.create(
        key=ProjectKey("DOCS"),
        name=ProjectName("Documentation Platform"),
        description=ProjectDescription("Document governance foundation."),
        now=datetime(2026, 8, 9, 10, 0, tzinfo=UTC),
    )


def _version(
    *,
    project_id: str,
    document_type: DocumentType,
    version_number: DocumentVersionNumber,
    created_at: datetime,
) -> DocumentVersion:
    version = DocumentVersion.create(
        document_id=DocumentId.new(),
        project_id=project_id,
        source_id="source-1",
        target_run_id="run-1",
        baseline_run_id=None,
        version_number=version_number,
        title="Governed document",
        file_name="governed-document.md",
        content=f"# {document_type.value}\n",
        operation_count=0,
        schema_count=0,
        breaking_change_count=0,
        revision_reason="Governance test.",
        created_by="Technical Writer",
        now=created_at,
    )
    version.document_type = document_type
    return version


def test_registry_query_returns_schema_version_and_ten_governed_types() -> None:
    project = _project()
    service = DocumentGovernanceApplicationService(
        DocumentRepositoryStub([]),
        ProjectRepositoryStub(project),
    )

    registry = asyncio.run(service.list_document_types())

    assert registry.schema_version == "document-type-registry-v1"
    assert registry.total == 10
    assert registry.items[0].document_type == "HLD"
    assert registry.items[-1].document_type == "DEVELOPER_ONBOARDING_BRIEF"


def test_project_checklist_uses_latest_governed_version_and_ignores_system_artifact() -> None:
    project = _project()
    now = datetime(2026, 8, 9, 10, 0, tzinfo=UTC)
    old_hld = _version(
        project_id=str(project.id),
        document_type=DocumentType.HLD,
        version_number=DocumentVersionNumber.first(),
        created_at=now,
    )
    latest_hld = _version(
        project_id=str(project.id),
        document_type=DocumentType.HLD,
        version_number=DocumentVersionNumber(major=1, minor=1),
        created_at=now + timedelta(minutes=1),
    )
    system_artifact = _version(
        project_id=str(project.id),
        document_type=DocumentType.TECHNICAL_SOURCE_OVERVIEW,
        version_number=DocumentVersionNumber.first(),
        created_at=now + timedelta(minutes=2),
    )
    service = DocumentGovernanceApplicationService(
        DocumentRepositoryStub([system_artifact, old_hld, latest_hld]),
        ProjectRepositoryStub(project),
    )

    checklist = asyncio.run(service.project_documentation_checklist(str(project.id)))

    assert checklist.policy_key == "project-documentation-baseline-v1"
    assert checklist.total == 10
    assert checklist.required_total == 7
    assert checklist.supplementary_total == 3
    assert checklist.available_total == 1
    assert checklist.missing_required_total == 6

    hld = next(item for item in checklist.items if item.document_type == "HLD")
    assert hld.availability == "AVAILABLE"
    assert hld.latest_version_id == str(latest_hld.id)
    assert hld.latest_version == "1.1"

    lld = next(item for item in checklist.items if item.document_type == "LLD")
    assert lld.availability == "MISSING"
    assert lld.latest_version_id is None
