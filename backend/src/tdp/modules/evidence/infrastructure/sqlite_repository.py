import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path

from tdp.modules.evidence.domain.model import (
    Claim,
    ClaimClassification,
    ClaimId,
    EvidenceArtifact,
    EvidenceArtifactId,
    EvidenceChecksum,
    EvidenceCollectionMethod,
    EvidenceKind,
    EvidenceSourceSystem,
)
from tdp.modules.evidence.domain.repository import EvidenceRepository

_SCHEMA = """
CREATE TABLE IF NOT EXISTS evidence_artifacts (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    feature_id TEXT,
    evidence_kind TEXT NOT NULL,
    source_system TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    origin_id TEXT NOT NULL,
    checksum TEXT NOT NULL,
    content_reference TEXT NOT NULL,
    collection_method TEXT NOT NULL,
    collected_by TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id),
    FOREIGN KEY(feature_id) REFERENCES features(id),
    UNIQUE(evidence_kind, origin_id)
);
CREATE INDEX IF NOT EXISTS idx_evidence_project_captured
ON evidence_artifacts(project_id, captured_at DESC, id ASC);

CREATE TABLE IF NOT EXISTS evidence_claims (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    feature_id TEXT,
    statement TEXT NOT NULL,
    classification TEXT NOT NULL,
    derivation_reference TEXT NOT NULL,
    asserted_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id),
    FOREIGN KEY(feature_id) REFERENCES features(id)
);
CREATE INDEX IF NOT EXISTS idx_evidence_claims_project_created
ON evidence_claims(project_id, created_at DESC, id ASC);

CREATE TABLE IF NOT EXISTS claim_evidence_references (
    claim_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    PRIMARY KEY(claim_id, evidence_id),
    FOREIGN KEY(claim_id) REFERENCES evidence_claims(id),
    FOREIGN KEY(evidence_id) REFERENCES evidence_artifacts(id)
);

CREATE TABLE IF NOT EXISTS claim_document_relevance (
    claim_id TEXT NOT NULL,
    document_type TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    PRIMARY KEY(claim_id, document_type),
    FOREIGN KEY(claim_id) REFERENCES evidence_claims(id)
);

CREATE TRIGGER IF NOT EXISTS evidence_artifacts_immutable_update
BEFORE UPDATE ON evidence_artifacts
BEGIN
    SELECT RAISE(ABORT, 'evidence artifacts are immutable');
END;

CREATE TRIGGER IF NOT EXISTS evidence_artifacts_immutable_delete
BEFORE DELETE ON evidence_artifacts
BEGIN
    SELECT RAISE(ABORT, 'evidence artifacts are immutable');
END;

CREATE TRIGGER IF NOT EXISTS evidence_claims_immutable_update
BEFORE UPDATE ON evidence_claims
BEGIN
    SELECT RAISE(ABORT, 'claims are immutable');
END;

CREATE TRIGGER IF NOT EXISTS evidence_claims_immutable_delete
BEFORE DELETE ON evidence_claims
BEGIN
    SELECT RAISE(ABORT, 'claims are immutable');
END;

CREATE TRIGGER IF NOT EXISTS claim_evidence_references_immutable_update
BEFORE UPDATE ON claim_evidence_references
BEGIN
    SELECT RAISE(ABORT, 'claim evidence references are immutable');
END;

CREATE TRIGGER IF NOT EXISTS claim_evidence_references_immutable_delete
BEFORE DELETE ON claim_evidence_references
BEGIN
    SELECT RAISE(ABORT, 'claim evidence references are immutable');
END;

CREATE TRIGGER IF NOT EXISTS claim_document_relevance_immutable_update
BEFORE UPDATE ON claim_document_relevance
BEGIN
    SELECT RAISE(ABORT, 'claim document relevance is immutable');
END;

CREATE TRIGGER IF NOT EXISTS claim_document_relevance_immutable_delete
BEFORE DELETE ON claim_document_relevance
BEGIN
    SELECT RAISE(ABORT, 'claim document relevance is immutable');
END;
"""


class SqliteEvidenceRepository(EvidenceRepository):
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    async def add_artifact(self, artifact: EvidenceArtifact) -> None:
        await asyncio.to_thread(self._add_artifact, artifact)

    async def get_artifact(
        self,
        artifact_id: EvidenceArtifactId,
    ) -> EvidenceArtifact | None:
        return await asyncio.to_thread(self._get_artifact, artifact_id)

    async def get_artifact_by_origin(
        self,
        kind: EvidenceKind,
        origin_id: str,
    ) -> EvidenceArtifact | None:
        return await asyncio.to_thread(self._get_artifact_by_origin, kind, origin_id)

    async def list_artifacts_by_project(
        self,
        project_id: str,
    ) -> list[EvidenceArtifact]:
        return await asyncio.to_thread(self._list_artifacts_by_project, project_id)

    async def add_claim(self, claim: Claim) -> None:
        await asyncio.to_thread(self._add_claim, claim)

    async def get_claim(self, claim_id: ClaimId) -> Claim | None:
        return await asyncio.to_thread(self._get_claim, claim_id)

    async def list_claims_by_project(self, project_id: str) -> list[Claim]:
        return await asyncio.to_thread(self._list_claims_by_project, project_id)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(_SCHEMA)

    def _add_artifact(self, artifact: EvidenceArtifact) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO evidence_artifacts (
                    id, workspace_id, project_id, feature_id, evidence_kind,
                    source_system, source_reference, origin_id, checksum,
                    content_reference, collection_method, collected_by,
                    captured_at, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._artifact_record(artifact),
            )

    def _get_artifact(
        self,
        artifact_id: EvidenceArtifactId,
    ) -> EvidenceArtifact | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM evidence_artifacts WHERE id = ?",
                (str(artifact_id),),
            ).fetchone()
        return self._artifact_from_row(row) if row is not None else None

    def _get_artifact_by_origin(
        self,
        kind: EvidenceKind,
        origin_id: str,
    ) -> EvidenceArtifact | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM evidence_artifacts
                WHERE evidence_kind = ? AND origin_id = ?
                """,
                (kind.value, origin_id),
            ).fetchone()
        return self._artifact_from_row(row) if row is not None else None

    def _list_artifacts_by_project(self, project_id: str) -> list[EvidenceArtifact]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM evidence_artifacts
                WHERE project_id = ?
                ORDER BY captured_at DESC, id ASC
                """,
                (project_id,),
            ).fetchall()
        return [self._artifact_from_row(row) for row in rows]

    def _add_claim(self, claim: Claim) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO evidence_claims (
                    id, workspace_id, project_id, feature_id, statement,
                    classification, derivation_reference, asserted_by, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(claim.id),
                    claim.workspace_id,
                    claim.project_id,
                    claim.feature_id,
                    claim.statement,
                    claim.classification.value,
                    claim.derivation_reference,
                    claim.asserted_by,
                    claim.created_at.isoformat(),
                ),
            )
            connection.executemany(
                """
                INSERT INTO claim_evidence_references (
                    claim_id, evidence_id, order_index
                )
                VALUES (?, ?, ?)
                """,
                [
                    (str(claim.id), str(evidence_id), index)
                    for index, evidence_id in enumerate(claim.evidence_ids)
                ],
            )
            connection.executemany(
                """
                INSERT INTO claim_document_relevance (
                    claim_id, document_type, order_index
                )
                VALUES (?, ?, ?)
                """,
                [
                    (str(claim.id), document_type, index)
                    for index, document_type in enumerate(claim.relevant_document_types)
                ],
            )

    def _get_claim(self, claim_id: ClaimId) -> Claim | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM evidence_claims WHERE id = ?",
                (str(claim_id),),
            ).fetchone()
            if row is None:
                return None
            return self._claim_from_row(connection, row)

    def _list_claims_by_project(self, project_id: str) -> list[Claim]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM evidence_claims
                WHERE project_id = ?
                ORDER BY created_at DESC, id ASC
                """,
                (project_id,),
            ).fetchall()
            return [self._claim_from_row(connection, row) for row in rows]

    @staticmethod
    def _artifact_record(artifact: EvidenceArtifact) -> tuple[object, ...]:
        return (
            str(artifact.id),
            artifact.workspace_id,
            artifact.project_id,
            artifact.feature_id,
            artifact.kind.value,
            artifact.source_system.value,
            artifact.source_reference,
            artifact.origin_id,
            str(artifact.checksum),
            artifact.content_reference,
            artifact.collection_method.value,
            artifact.collected_by,
            artifact.captured_at.isoformat(),
            artifact.created_at.isoformat(),
        )

    @staticmethod
    def _artifact_from_row(row: sqlite3.Row) -> EvidenceArtifact:
        return EvidenceArtifact(
            id=EvidenceArtifactId.from_string(str(row["id"])),
            workspace_id=str(row["workspace_id"]),
            project_id=str(row["project_id"]),
            feature_id=str(row["feature_id"]) if row["feature_id"] is not None else None,
            kind=EvidenceKind(str(row["evidence_kind"])),
            source_system=EvidenceSourceSystem(str(row["source_system"])),
            source_reference=str(row["source_reference"]),
            origin_id=str(row["origin_id"]),
            checksum=EvidenceChecksum(str(row["checksum"])),
            content_reference=str(row["content_reference"]),
            collection_method=EvidenceCollectionMethod(str(row["collection_method"])),
            collected_by=str(row["collected_by"]),
            captured_at=datetime.fromisoformat(str(row["captured_at"])),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )

    @staticmethod
    def _claim_from_row(connection: sqlite3.Connection, row: sqlite3.Row) -> Claim:
        evidence_rows = connection.execute(
            """
            SELECT evidence_id FROM claim_evidence_references
            WHERE claim_id = ?
            ORDER BY order_index ASC
            """,
            (str(row["id"]),),
        ).fetchall()
        document_rows = connection.execute(
            """
            SELECT document_type FROM claim_document_relevance
            WHERE claim_id = ?
            ORDER BY order_index ASC
            """,
            (str(row["id"]),),
        ).fetchall()

        return Claim(
            id=ClaimId.from_string(str(row["id"])),
            workspace_id=str(row["workspace_id"]),
            project_id=str(row["project_id"]),
            feature_id=str(row["feature_id"]) if row["feature_id"] is not None else None,
            statement=str(row["statement"]),
            classification=ClaimClassification(str(row["classification"])),
            evidence_ids=tuple(
                EvidenceArtifactId.from_string(str(item["evidence_id"])) for item in evidence_rows
            ),
            derivation_reference=str(row["derivation_reference"]),
            relevant_document_types=tuple(str(item["document_type"]) for item in document_rows),
            asserted_by=str(row["asserted_by"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )
