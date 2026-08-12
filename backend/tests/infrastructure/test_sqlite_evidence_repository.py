import asyncio
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tdp.modules.evidence.domain.materialization import (
    EvidenceMaterialization,
    canonicalize_semantic_evidence_manifest,
)
from tdp.modules.evidence.domain.model import (
    Claim,
    ClaimClassification,
    EvidenceArtifact,
    EvidenceCollectionMethod,
    EvidenceKind,
    EvidenceSourceSystem,
)
from tdp.modules.evidence.infrastructure.sqlite_repository import SqliteEvidenceRepository


def _create_parent_tables(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE projects (id TEXT PRIMARY KEY);
            CREATE TABLE features (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL
            );
            INSERT INTO projects (id) VALUES ('project-1');
            """
        )


def _artifact() -> EvidenceArtifact:
    return EvidenceArtifact.create(
        workspace_id="workspace-1",
        project_id="project-1",
        kind=EvidenceKind.SOURCE_ARTIFACT,
        source_system=EvidenceSourceSystem.SOURCE_REGISTRY,
        source_reference="source:source-1",
        origin_id="source-1",
        checksum="b" * 64,
        content_reference="source-artifact:source-1",
        collection_method=EvidenceCollectionMethod.SOURCE_IMPORT,
        collected_by="Technical Writer",
        captured_at=datetime(2026, 8, 10, 2, 0, tzinfo=UTC),
    )


def test_repository_round_trips_immutable_evidence_and_claim_links(tmp_path: Path) -> None:
    database_path = tmp_path / "evidence.sqlite3"
    _create_parent_tables(database_path)
    repository = SqliteEvidenceRepository(database_path)
    artifact = _artifact()
    asyncio.run(repository.add_artifact(artifact))

    claim = Claim.create(
        workspace_id="workspace-1",
        project_id="project-1",
        statement="The imported OpenAPI file is registered evidence.",
        classification=ClaimClassification.OBSERVED,
        evidence_ids=(artifact.id,),
        derivation_reference="",
        relevant_document_types=("LLD", "AS_BUILT"),
        asserted_by="Technical Writer",
        now=datetime(2026, 8, 10, 2, 5, tzinfo=UTC),
    )
    asyncio.run(repository.add_claim(claim))

    restored_artifact = asyncio.run(repository.get_artifact(artifact.id))
    restored_claim = asyncio.run(repository.get_claim(claim.id))

    assert restored_artifact == artifact
    assert restored_claim == claim


def test_sqlite_guards_evidence_and_claim_history_from_update_or_delete(tmp_path: Path) -> None:
    database_path = tmp_path / "immutable.sqlite3"
    _create_parent_tables(database_path)
    repository = SqliteEvidenceRepository(database_path)
    artifact = _artifact()
    asyncio.run(repository.add_artifact(artifact))

    claim = Claim.create(
        workspace_id="workspace-1",
        project_id="project-1",
        statement="The source checksum is immutable.",
        classification=ClaimClassification.OBSERVED,
        evidence_ids=(artifact.id,),
        derivation_reference="",
        relevant_document_types=("AS_BUILT",),
        asserted_by="Technical Writer",
    )
    asyncio.run(repository.add_claim(claim))

    with sqlite3.connect(database_path) as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE evidence_artifacts SET checksum = ? WHERE id = ?",
            ("c" * 64, str(artifact.id)),
        )

    with sqlite3.connect(database_path) as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "DELETE FROM evidence_claims WHERE id = ?",
            (str(claim.id),),
        )


def test_repository_persists_new_semantic_evidence_without_schema_migration(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "semantic-evidence.sqlite3"
    _create_parent_tables(database_path)
    repository = SqliteEvidenceRepository(database_path)
    artifact = EvidenceArtifact.create(
        workspace_id="workspace-1",
        project_id="project-1",
        kind=EvidenceKind.DEPLOYMENT_RUNTIME,
        source_system=EvidenceSourceSystem.GOVERNED_REFERENCE,
        source_reference="deployment-run:release-2026-08-12",
        origin_id="release-2026-08-12",
        checksum="e" * 64,
        content_reference="evidence-manifest:release-2026-08-12",
        collection_method=EvidenceCollectionMethod.REFERENCE_REGISTRATION,
        collected_by="Release Engineer",
        captured_at=datetime(2026, 8, 12, 2, 0, tzinfo=UTC),
    )

    asyncio.run(repository.add_artifact(artifact))
    restored = asyncio.run(repository.get_artifact(artifact.id))

    assert restored == artifact
    assert restored is not None
    assert restored.kind is EvidenceKind.DEPLOYMENT_RUNTIME


def test_repository_round_trips_and_guards_materialized_semantic_facts(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "materialized-evidence.sqlite3"
    _create_parent_tables(database_path)
    repository = SqliteEvidenceRepository(database_path)
    manifest = {
        "schema_version": "semantic-evidence-manifest-v1",
        "kind": "DEPLOYMENT_RUNTIME",
        "payload": {
            "environment": "staging",
            "runtime_components": [
                {
                    "name": "api",
                    "version": "1.4.0",
                    "source_reference": "deployment-run:release-42",
                }
            ],
            "prerequisites": ["Container runtime is available."],
            "configuration_keys": ["DATABASE_URL"],
            "deployment_steps": [
                {
                    "sequence": 1,
                    "instruction": "Apply the approved deployment bundle.",
                    "source_reference": "pipeline-step:deploy",
                }
            ],
            "verification_checks": [
                {
                    "name": "Readiness endpoint",
                    "expected_result": "The service reports healthy.",
                    "source_reference": "pipeline-step:verify",
                }
            ],
            "rollback_references": ["runbook:rollback-release-42"],
        },
    }
    canonical = canonicalize_semantic_evidence_manifest(
        EvidenceKind.DEPLOYMENT_RUNTIME,
        manifest,
    )
    artifact = EvidenceArtifact.create(
        workspace_id="workspace-1",
        project_id="project-1",
        kind=EvidenceKind.DEPLOYMENT_RUNTIME,
        source_system=EvidenceSourceSystem.GOVERNED_REFERENCE,
        source_reference="deployment-run:release-42",
        origin_id="release-42",
        checksum=str(canonical.checksum),
        content_reference="evidence-manifest:release-42",
        collection_method=EvidenceCollectionMethod.REFERENCE_REGISTRATION,
        collected_by="Release Engineer",
        captured_at=datetime(2026, 8, 12, 4, 0, tzinfo=UTC),
    )
    asyncio.run(repository.add_artifact(artifact))
    materialization = EvidenceMaterialization.create(
        evidence_id=artifact.id,
        project_id="project-1",
        expected_checksum=artifact.checksum,
        manifest=canonical,
        materialized_by="Release Engineer",
        materialized_at=datetime(2026, 8, 12, 4, 5, tzinfo=UTC),
    )
    asyncio.run(repository.add_materialization(materialization))

    restored = asyncio.run(repository.get_materialization(artifact.id))
    by_project = asyncio.run(repository.list_materializations_by_project("project-1"))

    assert restored == materialization
    assert by_project == [materialization]

    with sqlite3.connect(database_path) as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE evidence_materializations SET checksum = ? WHERE evidence_id = ?",
            ("f" * 64, str(artifact.id)),
        )
