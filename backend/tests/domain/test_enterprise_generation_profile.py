from tdp.modules.documents.domain.generation import (
    ENTERPRISE_GENERATION_PROFILE_SCHEMA_VERSION,
    ENTERPRISE_GENERATION_PROFILES,
    enterprise_generation_profile,
)
from tdp.modules.documents.domain.model import (
    DocumentId,
    DocumentType,
    DocumentVersion,
    DocumentVersionNumber,
)


def test_generation_profile_foundation_starts_with_lld_only() -> None:
    assert ENTERPRISE_GENERATION_PROFILE_SCHEMA_VERSION == "enterprise-generation-profile-v1"
    assert [profile.document_type for profile in ENTERPRISE_GENERATION_PROFILES] == [
        DocumentType.LLD
    ]
    profile = enterprise_generation_profile(DocumentType.LLD)
    assert profile is not None
    assert profile.profile_key == "enterprise-lld-v1"
    assert profile.primary_evidence_kind == "CATALOG_SNAPSHOT"
    assert profile.rendered_claim_classifications == ("OBSERVED", "INFERRED")
    assert enterprise_generation_profile(DocumentType.AS_BUILT) is None


def test_document_version_can_create_governed_enterprise_type_without_mutation() -> None:
    version = DocumentVersion.create(
        document_id=DocumentId.new(),
        project_id="project-1",
        source_id="source-1",
        target_run_id="run-1",
        baseline_run_id=None,
        version_number=DocumentVersionNumber.first(),
        title="Low Level Design",
        file_name="lld-v1.0.md",
        content="# Low Level Design\n",
        operation_count=1,
        schema_count=1,
        breaking_change_count=0,
        revision_reason="Initial governed LLD.",
        created_by="Technical Writer",
        document_type=DocumentType.LLD,
    )

    assert version.document_type is DocumentType.LLD
