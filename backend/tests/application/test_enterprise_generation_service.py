import asyncio

import pytest

from tdp.identity.model import IdentityAssurance, RequestPrincipal
from tdp.modules.documents.application.commands import GenerateEnterpriseDocumentCommand
from tdp.modules.documents.application.enterprise_generation_ports import (
    EnterpriseGenerationContext,
    GenerationEvidenceFact,
)
from tdp.modules.documents.application.enterprise_generation_service import (
    EnterpriseDocumentGenerationService,
)
from tdp.modules.documents.domain.errors import EnterpriseDocumentGenerationBlockedError
from tdp.modules.documents.domain.generation import (
    EnterpriseDocumentGenerationProfile,
    GenerationReadinessFinding,
    GenerationReadinessSnapshot,
    enterprise_generation_profile,
)
from tdp.modules.documents.domain.model import (
    DocumentSeries,
    DocumentType,
    DocumentVersion,
)


class DocumentRepositoryStub:
    def __init__(self) -> None:
        self.series: DocumentSeries | None = None
        self.versions: list[DocumentVersion] = []

    async def get_series_by_project_type(
        self,
        _project_id: str,
        _document_type: DocumentType,
    ) -> DocumentSeries | None:
        return self.series

    async def find_version_by_checksum(
        self,
        _document_id: object,
        checksum: str,
    ) -> DocumentVersion | None:
        return next((item for item in self.versions if item.checksum == checksum), None)

    async def list_versions(self, _document_id: object) -> list[DocumentVersion]:
        return list(reversed(self.versions))

    async def add_version(
        self,
        series: DocumentSeries,
        version: DocumentVersion,
        _event: object,
    ) -> None:
        self.series = series
        self.versions.append(version)


class InputProviderStub:
    def __init__(self, readiness: GenerationReadinessSnapshot) -> None:
        self.readiness_value = readiness
        self.collect_calls = 0

    async def readiness(
        self,
        _project_id: str,
        _profile: EnterpriseDocumentGenerationProfile,
    ) -> GenerationReadinessSnapshot:
        return self.readiness_value

    async def collect(
        self,
        project_id: str,
        profile: EnterpriseDocumentGenerationProfile,
    ) -> EnterpriseGenerationContext:
        self.collect_calls += 1
        return _context(project_id, profile)


class RendererStub:
    def render(self, context: EnterpriseGenerationContext) -> str:
        return (
            f"# {context.profile.display_name}: {context.project_name}\n\n"
            f"Evidence: {context.primary_evidence_id}\n"
        )


def _principal() -> RequestPrincipal:
    return RequestPrincipal(
        subject_id="local-user",
        display_name="Technical Writer",
        email="writer@example.test",
        provider="local",
        assurance=IdentityAssurance.DEVELOPMENT,
    )


def _context(
    project_id: str,
    profile: EnterpriseDocumentGenerationProfile | None = None,
) -> EnterpriseGenerationContext:
    selected_profile = profile or enterprise_generation_profile(DocumentType.LLD)
    assert selected_profile is not None
    readiness = GenerationReadinessSnapshot(
        policy_version="document-readiness-v1",
        state="READY",
        eligible=True,
        findings=(),
    )
    return EnterpriseGenerationContext(
        profile=selected_profile,
        readiness=readiness,
        project_id=project_id,
        project_key="DOCS",
        project_name="Documentation Platform",
        project_description="Source-backed documentation.",
        workspace_id="workspace-1",
        source_id="source-1",
        source_name="Core API",
        api_title="Core API",
        api_version="1.0.0",
        openapi_version="3.1.0",
        target_run_id="run-1",
        source_checksum="a" * 64,
        snapshot_completed_at="2026-08-10T10:00:00+00:00",
        primary_evidence_id="evidence-1",
        primary_evidence_kind="CATALOG_SNAPSHOT",
        available_snapshot_count=1,
        evidence=(
            GenerationEvidenceFact(
                id="evidence-1",
                kind="CATALOG_SNAPSHOT",
                checksum="b" * 64,
                source_reference="synchronization:run-1",
                content_reference="catalog-snapshot:run-1",
                captured_at="2026-08-10T10:00:00+00:00",
            ),
        ),
        claims=(),
        operations=(),
        schemas=(),
    )


def test_generation_is_blocked_before_inputs_are_collected() -> None:
    finding = GenerationReadinessFinding(
        rule_code="LLD_NORMALIZED_TECHNICAL_EVIDENCE_REQUIRED",
        severity="BLOCKER",
        message="Normalized evidence is required.",
        missing_input="evidence-kind:CATALOG_SNAPSHOT",
        remediation="Register a Catalog snapshot.",
        supporting_references=(),
    )
    provider = InputProviderStub(
        GenerationReadinessSnapshot(
            policy_version="document-readiness-v1",
            state="NOT_READY",
            eligible=False,
            findings=(finding,),
        )
    )
    service = EnterpriseDocumentGenerationService(
        DocumentRepositoryStub(),
        provider,
        RendererStub(),
    )

    with pytest.raises(EnterpriseDocumentGenerationBlockedError) as exc_info:
        asyncio.run(
            service.generate(
                GenerateEnterpriseDocumentCommand(
                    project_id="project-1",
                    document_type="LLD",
                    principal=_principal(),
                )
            )
        )

    assert exc_info.value.findings == (finding,)
    assert provider.collect_calls == 0


def test_generation_creates_and_reuses_immutable_lld_version() -> None:
    repository = DocumentRepositoryStub()
    provider = InputProviderStub(
        GenerationReadinessSnapshot(
            policy_version="document-readiness-v1",
            state="READY",
            eligible=True,
            findings=(),
        )
    )
    service = EnterpriseDocumentGenerationService(repository, provider, RendererStub())
    command = GenerateEnterpriseDocumentCommand(
        project_id="project-1",
        document_type="LLD",
        principal=_principal(),
        revision_reason="Generate governed LLD.",
    )

    first = asyncio.run(service.generate(command))
    duplicate = asyncio.run(service.generate(command))

    assert first.document_type == "LLD"
    assert first.version == "1.0"
    assert first.reused_existing_version is False
    assert duplicate.id == first.id
    assert duplicate.reused_existing_version is True
    assert len(repository.versions) == 1
    provenance = repository.versions[0].provenance
    assert any(
        item.kind.value == "EVIDENCE_ARTIFACT"
        and item.reference == "evidence:evidence-1"
        and item.evidence_kind == "CATALOG_SNAPSHOT"
        and item.checksum == "b" * 64
        for item in provenance
    )


def test_same_generic_service_creates_as_built_version() -> None:
    repository = DocumentRepositoryStub()
    provider = InputProviderStub(
        GenerationReadinessSnapshot(
            policy_version="document-readiness-v1",
            state="READY",
            eligible=True,
            findings=(),
        )
    )
    service = EnterpriseDocumentGenerationService(repository, provider, RendererStub())

    result = asyncio.run(
        service.generate(
            GenerateEnterpriseDocumentCommand(
                project_id="project-1",
                document_type="AS_BUILT",
                principal=_principal(),
                revision_reason="Generate governed As-Built draft.",
            )
        )
    )

    assert result.document_type == "AS_BUILT"
    assert result.version == "1.0"
    assert result.file_name == "docs-as-built-documentation-v1.0.md"
    assert provider.collect_calls == 1
