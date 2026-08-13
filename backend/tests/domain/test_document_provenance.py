from tdp.modules.documents.domain.model import (
    DocumentId,
    DocumentProvenanceKind,
    DocumentProvenanceReference,
    DocumentType,
    DocumentVersion,
    DocumentVersionNumber,
)


def test_document_version_accepts_source_free_evidence_provenance() -> None:
    evidence = DocumentProvenanceReference.evidence_artifact(
        evidence_id="evidence-1",
        evidence_kind="DEPLOYMENT_RUNTIME",
        checksum="a" * 64,
    )

    version = DocumentVersion.create(
        document_id=DocumentId.new(),
        project_id="project-1",
        source_id=None,
        target_run_id=None,
        baseline_run_id=None,
        version_number=DocumentVersionNumber.first(),
        title="Installation Guide",
        file_name="installation-guide-v1.0.md",
        content="# Installation Guide\n",
        operation_count=0,
        schema_count=0,
        breaking_change_count=0,
        revision_reason="Governed deployment evidence.",
        created_by="Technical Writer",
        document_type=DocumentType.INSTALLATION_GUIDE,
        provenance=(evidence,),
    )

    assert version.source_id is None
    assert version.target_run_id is None
    assert version.provenance == (evidence,)
    assert version.provenance[0].kind is DocumentProvenanceKind.EVIDENCE_ARTIFACT


def test_document_version_merges_legacy_and_evidence_provenance_deterministically() -> None:
    evidence = DocumentProvenanceReference.evidence_artifact(
        evidence_id="evidence-2",
        evidence_kind="CATALOG_SNAPSHOT",
        checksum="b" * 64,
    )

    version = DocumentVersion.create(
        document_id=DocumentId.new(),
        project_id="project-1",
        source_id="source-1",
        target_run_id="run-1",
        baseline_run_id=None,
        version_number=DocumentVersionNumber.first(),
        title="Low Level Design",
        file_name="lld-v1.0.md",
        content="# LLD\n",
        operation_count=1,
        schema_count=1,
        breaking_change_count=0,
        revision_reason="Governed catalog evidence.",
        created_by="Technical Writer",
        document_type=DocumentType.LLD,
        provenance=(evidence, evidence),
    )

    assert [(item.kind.value, item.reference) for item in version.provenance] == [
        ("SOURCE_REGISTRY", "source:source-1"),
        ("CATALOG_SYNCHRONIZATION", "synchronization:run-1"),
        ("EVIDENCE_ARTIFACT", "evidence:evidence-2"),
    ]
