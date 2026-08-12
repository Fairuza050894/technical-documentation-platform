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


def test_generation_profiles_cover_lld_as_built_and_hld_in_rollout_order() -> None:
    assert ENTERPRISE_GENERATION_PROFILE_SCHEMA_VERSION == "enterprise-generation-profile-v2"
    assert [profile.document_type for profile in ENTERPRISE_GENERATION_PROFILES] == [
        DocumentType.LLD,
        DocumentType.AS_BUILT,
        DocumentType.HLD,
    ]

    lld = enterprise_generation_profile(DocumentType.LLD)
    assert lld is not None
    assert lld.profile_key == "enterprise-lld-v1"
    assert lld.accepted_evidence_kinds == ("CATALOG_SNAPSHOT",)
    assert lld.primary_evidence_kind == "CATALOG_SNAPSHOT"
    assert lld.rendered_claim_classifications == ("OBSERVED", "INFERRED")

    as_built = enterprise_generation_profile(DocumentType.AS_BUILT)
    assert as_built is not None
    assert as_built.profile_key == "enterprise-as-built-v1"
    assert as_built.accepted_evidence_kinds == ("CATALOG_SNAPSHOT",)
    assert as_built.primary_evidence_kind == "CATALOG_SNAPSHOT"
    assert as_built.rendered_claim_classifications == ("OBSERVED",)

    hld = enterprise_generation_profile(DocumentType.HLD)
    assert hld is not None
    assert hld.profile_key == "enterprise-hld-v1"
    assert hld.accepted_evidence_kinds == ("CATALOG_SNAPSHOT", "SOURCE_ARTIFACT")
    assert hld.rendered_claim_classifications == ("OBSERVED", "INFERRED")


def test_document_version_can_create_governed_enterprise_type_without_snapshot() -> None:
    version = DocumentVersion.create(
        document_id=DocumentId.new(),
        project_id="project-1",
        source_id="source-1",
        target_run_id=None,
        baseline_run_id=None,
        version_number=DocumentVersionNumber.first(),
        title="High Level Design",
        file_name="hld-v1.0.md",
        content="# High Level Design\n",
        operation_count=0,
        schema_count=0,
        breaking_change_count=0,
        revision_reason="Initial governed HLD.",
        created_by="Technical Writer",
        document_type=DocumentType.HLD,
    )

    assert version.document_type is DocumentType.HLD
    assert version.target_run_id is None
