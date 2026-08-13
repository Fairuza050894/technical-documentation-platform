import asyncio
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from tdp.modules.documents.domain.model import (
    DocumentFormat,
    DocumentId,
    DocumentProvenanceKind,
    DocumentProvenanceReference,
    DocumentSeries,
    DocumentStatus,
    DocumentType,
    DocumentVersion,
    DocumentVersionId,
    DocumentVersionNumber,
    DocumentWorkflowEvent,
    WorkflowAction,
    WorkflowEventId,
)
from tdp.modules.documents.domain.repository import DocumentRepository

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    document_type TEXT NOT NULL,
    title TEXT NOT NULL,
    current_version_id TEXT,
    current_approved_version_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, document_type),
    FOREIGN KEY(project_id) REFERENCES projects(id)
);
CREATE INDEX IF NOT EXISTS idx_documents_project_type
ON documents(project_id, document_type);

CREATE TABLE IF NOT EXISTS document_versions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    source_id TEXT,
    target_run_id TEXT,
    baseline_run_id TEXT,
    document_type TEXT NOT NULL,
    document_format TEXT NOT NULL,
    version_major INTEGER NOT NULL,
    version_minor INTEGER NOT NULL,
    status TEXT NOT NULL,
    title TEXT NOT NULL,
    file_name TEXT NOT NULL,
    content TEXT NOT NULL,
    checksum TEXT NOT NULL,
    operation_count INTEGER NOT NULL,
    schema_count INTEGER NOT NULL,
    breaking_change_count INTEGER NOT NULL,
    revision_reason TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    submitted_at TEXT,
    approved_at TEXT,
    superseded_at TEXT,
    UNIQUE(document_id, version_major, version_minor),
    UNIQUE(document_id, checksum),
    FOREIGN KEY(document_id) REFERENCES documents(id),
    FOREIGN KEY(project_id) REFERENCES projects(id),
    FOREIGN KEY(source_id) REFERENCES sources(id),
    FOREIGN KEY(target_run_id) REFERENCES catalog_sync_runs(id),
    FOREIGN KEY(baseline_run_id) REFERENCES catalog_sync_runs(id)
);
CREATE INDEX IF NOT EXISTS idx_document_versions_project_created
ON document_versions(project_id, created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_document_versions_document_number
ON document_versions(document_id, version_major DESC, version_minor DESC);
CREATE INDEX IF NOT EXISTS idx_document_versions_status
ON document_versions(document_id, status, approved_at DESC);

CREATE TABLE IF NOT EXISTS document_version_provenance (
    version_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    provenance_kind TEXT NOT NULL,
    provenance_reference TEXT NOT NULL,
    evidence_kind TEXT,
    checksum TEXT,
    PRIMARY KEY(version_id, ordinal),
    UNIQUE(version_id, provenance_kind, provenance_reference),
    FOREIGN KEY(version_id) REFERENCES document_versions(id)
);
CREATE INDEX IF NOT EXISTS idx_document_version_provenance_reference
ON document_version_provenance(provenance_kind, provenance_reference, version_id);

CREATE TRIGGER IF NOT EXISTS document_version_provenance_immutable_update
BEFORE UPDATE ON document_version_provenance
BEGIN
    SELECT RAISE(ABORT, 'document version provenance is immutable');
END;

CREATE TRIGGER IF NOT EXISTS document_version_provenance_immutable_delete
BEFORE DELETE ON document_version_provenance
BEGIN
    SELECT RAISE(ABORT, 'document version provenance is immutable');
END;

CREATE TABLE IF NOT EXISTS document_workflow_events (
    id TEXT PRIMARY KEY,
    version_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT NOT NULL,
    comment TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(version_id) REFERENCES document_versions(id)
);
CREATE INDEX IF NOT EXISTS idx_document_workflow_events_version_created
ON document_workflow_events(version_id, created_at ASC, id ASC);
"""


class SqliteDocumentRepository(DocumentRepository):
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    async def get_series(self, document_id: DocumentId) -> DocumentSeries | None:
        return await asyncio.to_thread(self._get_series, document_id)

    async def get_series_by_project_type(
        self,
        project_id: str,
        document_type: DocumentType,
    ) -> DocumentSeries | None:
        return await asyncio.to_thread(
            self._get_series_by_project_type,
            project_id,
            document_type,
        )

    async def add_version(
        self,
        series: DocumentSeries,
        version: DocumentVersion,
        event: DocumentWorkflowEvent,
    ) -> None:
        await asyncio.to_thread(self._add_version, series, version, event)

    async def get_version(self, version_id: DocumentVersionId) -> DocumentVersion | None:
        return await asyncio.to_thread(self._get_version, version_id)

    async def find_version_by_checksum(
        self,
        document_id: DocumentId,
        checksum: str,
    ) -> DocumentVersion | None:
        return await asyncio.to_thread(
            self._find_version_by_checksum,
            document_id,
            checksum,
        )

    async def get_current_approved_version(
        self,
        document_id: DocumentId,
    ) -> DocumentVersion | None:
        return await asyncio.to_thread(self._get_current_approved_version, document_id)

    async def list_versions_by_project(self, project_id: str) -> list[DocumentVersion]:
        return await asyncio.to_thread(self._list_versions_by_project, project_id)

    async def list_versions(self, document_id: DocumentId) -> list[DocumentVersion]:
        return await asyncio.to_thread(self._list_versions, document_id)

    async def apply_workflow_transition(
        self,
        series: DocumentSeries,
        version: DocumentVersion,
        event: DocumentWorkflowEvent,
        *,
        superseded_version: DocumentVersion | None = None,
        superseded_event: DocumentWorkflowEvent | None = None,
    ) -> None:
        await asyncio.to_thread(
            self._apply_workflow_transition,
            series,
            version,
            event,
            superseded_version,
            superseded_event,
        )

    async def list_workflow_events(
        self,
        version_id: DocumentVersionId,
    ) -> list[DocumentWorkflowEvent]:
        return await asyncio.to_thread(self._list_workflow_events, version_id)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(_SCHEMA)
            self._migrate_nullable_document_provenance(connection)
            self._migrate_generated_documents(connection)
            self._backfill_document_version_provenance(connection)

    @staticmethod
    def _migrate_nullable_document_provenance(connection: sqlite3.Connection) -> None:
        columns = {
            str(row["name"]): row
            for row in connection.execute("PRAGMA table_info(document_versions)").fetchall()
        }
        source_column = columns.get("source_id")
        target_column = columns.get("target_run_id")
        if source_column is None or target_column is None:
            return
        if int(source_column["notnull"]) == 0 and int(target_column["notnull"]) == 0:
            return

        connection.commit()
        connection.execute("PRAGMA foreign_keys = OFF")
        try:
            connection.executescript(
                """
                BEGIN IMMEDIATE;
                CREATE TABLE document_versions_nullable_provenance (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    source_id TEXT,
                    target_run_id TEXT,
                    baseline_run_id TEXT,
                    document_type TEXT NOT NULL,
                    document_format TEXT NOT NULL,
                    version_major INTEGER NOT NULL,
                    version_minor INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    title TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    operation_count INTEGER NOT NULL,
                    schema_count INTEGER NOT NULL,
                    breaking_change_count INTEGER NOT NULL,
                    revision_reason TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    submitted_at TEXT,
                    approved_at TEXT,
                    superseded_at TEXT,
                    UNIQUE(document_id, version_major, version_minor),
                    UNIQUE(document_id, checksum),
                    FOREIGN KEY(document_id) REFERENCES documents(id),
                    FOREIGN KEY(project_id) REFERENCES projects(id),
                    FOREIGN KEY(source_id) REFERENCES sources(id),
                    FOREIGN KEY(target_run_id) REFERENCES catalog_sync_runs(id),
                    FOREIGN KEY(baseline_run_id) REFERENCES catalog_sync_runs(id)
                );
                INSERT INTO document_versions_nullable_provenance (
                    id, document_id, project_id, source_id, target_run_id,
                    baseline_run_id, document_type, document_format,
                    version_major, version_minor, status, title, file_name,
                    content, checksum, operation_count, schema_count,
                    breaking_change_count, revision_reason, created_by,
                    created_at, updated_at, submitted_at, approved_at, superseded_at
                )
                SELECT
                    id, document_id, project_id, source_id, target_run_id,
                    baseline_run_id, document_type, document_format,
                    version_major, version_minor, status, title, file_name,
                    content, checksum, operation_count, schema_count,
                    breaking_change_count, revision_reason, created_by,
                    created_at, updated_at, submitted_at, approved_at, superseded_at
                FROM document_versions;
                DROP TABLE document_versions;
                ALTER TABLE document_versions_nullable_provenance RENAME TO document_versions;
                CREATE INDEX idx_document_versions_project_created
                ON document_versions(project_id, created_at DESC, id DESC);
                CREATE INDEX idx_document_versions_document_number
                ON document_versions(document_id, version_major DESC, version_minor DESC);
                CREATE INDEX idx_document_versions_status
                ON document_versions(document_id, status, approved_at DESC);
                COMMIT;
                """
            )
        except Exception:
            if connection.in_transaction:
                connection.rollback()
            raise
        finally:
            connection.execute("PRAGMA foreign_keys = ON")

    def _get_series(self, document_id: DocumentId) -> DocumentSeries | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE id = ?",
                (str(document_id),),
            ).fetchone()
        return self._series_from_row(row) if row is not None else None

    def _get_series_by_project_type(
        self,
        project_id: str,
        document_type: DocumentType,
    ) -> DocumentSeries | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM documents
                WHERE project_id = ? AND document_type = ?
                """,
                (project_id, document_type.value),
            ).fetchone()
        return self._series_from_row(row) if row is not None else None

    def _add_version(
        self,
        series: DocumentSeries,
        version: DocumentVersion,
        event: DocumentWorkflowEvent,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    id, project_id, document_type, title, current_version_id,
                    current_approved_version_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    current_version_id = excluded.current_version_id,
                    current_approved_version_id = excluded.current_approved_version_id,
                    updated_at = excluded.updated_at
                """,
                self._series_record(series),
            )
            connection.execute(
                """
                INSERT INTO document_versions (
                    id, document_id, project_id, source_id, target_run_id,
                    baseline_run_id, document_type, document_format,
                    version_major, version_minor, status, title, file_name,
                    content, checksum, operation_count, schema_count,
                    breaking_change_count, revision_reason, created_by,
                    created_at, updated_at, submitted_at, approved_at, superseded_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                )
                """,
                self._version_record(version),
            )
            for ordinal, provenance in enumerate(version.provenance):
                connection.execute(
                    """
                    INSERT INTO document_version_provenance (
                        version_id, ordinal, provenance_kind,
                        provenance_reference, evidence_kind, checksum
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    self._provenance_record(version.id, ordinal, provenance),
                )
            connection.execute(
                """
                INSERT INTO document_workflow_events (
                    id, version_id, actor, action, previous_status,
                    new_status, comment, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._event_record(event),
            )

    def _get_version(self, version_id: DocumentVersionId) -> DocumentVersion | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM document_versions WHERE id = ?",
                (str(version_id),),
            ).fetchone()
        return self._version_from_row(row) if row is not None else None

    def _find_version_by_checksum(
        self,
        document_id: DocumentId,
        checksum: str,
    ) -> DocumentVersion | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM document_versions
                WHERE document_id = ? AND checksum = ?
                LIMIT 1
                """,
                (str(document_id), checksum),
            ).fetchone()
        return self._version_from_row(row) if row is not None else None

    def _get_current_approved_version(
        self,
        document_id: DocumentId,
    ) -> DocumentVersion | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT version.*
                FROM documents AS document
                JOIN document_versions AS version
                  ON version.id = document.current_approved_version_id
                WHERE document.id = ?
                """,
                (str(document_id),),
            ).fetchone()
        return self._version_from_row(row) if row is not None else None

    def _list_versions_by_project(self, project_id: str) -> list[DocumentVersion]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM document_versions
                WHERE project_id = ?
                ORDER BY created_at DESC, version_major DESC, version_minor DESC, id DESC
                """,
                (project_id,),
            ).fetchall()
        return [self._version_from_row(row) for row in rows]

    def _list_versions(self, document_id: DocumentId) -> list[DocumentVersion]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM document_versions
                WHERE document_id = ?
                ORDER BY version_major DESC, version_minor DESC, created_at DESC, id DESC
                """,
                (str(document_id),),
            ).fetchall()
        return [self._version_from_row(row) for row in rows]

    def _apply_workflow_transition(
        self,
        series: DocumentSeries,
        version: DocumentVersion,
        event: DocumentWorkflowEvent,
        superseded_version: DocumentVersion | None,
        superseded_event: DocumentWorkflowEvent | None,
    ) -> None:
        if (superseded_version is None) is not (superseded_event is None):
            raise ValueError("Superseded version and event must be supplied together.")

        with self._connect() as connection:
            self._update_version(connection, version)
            connection.execute(
                """
                INSERT INTO document_workflow_events (
                    id, version_id, actor, action, previous_status,
                    new_status, comment, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._event_record(event),
            )
            if superseded_version is not None and superseded_event is not None:
                self._update_version(connection, superseded_version)
                connection.execute(
                    """
                    INSERT INTO document_workflow_events (
                        id, version_id, actor, action, previous_status,
                        new_status, comment, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    self._event_record(superseded_event),
                )
            connection.execute(
                """
                UPDATE documents
                SET title = ?, current_version_id = ?, current_approved_version_id = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    series.title,
                    series.current_version_id,
                    series.current_approved_version_id,
                    series.updated_at.isoformat(),
                    str(series.id),
                ),
            )

    def _list_workflow_events(
        self,
        version_id: DocumentVersionId,
    ) -> list[DocumentWorkflowEvent]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM document_workflow_events
                WHERE version_id = ?
                ORDER BY created_at ASC, id ASC
                """,
                (str(version_id),),
            ).fetchall()
        return [self._event_from_row(row) for row in rows]

    @staticmethod
    def _update_version(connection: sqlite3.Connection, version: DocumentVersion) -> None:
        connection.execute(
            """
            UPDATE document_versions
            SET status = ?, updated_at = ?, submitted_at = ?, approved_at = ?,
                superseded_at = ?
            WHERE id = ?
            """,
            (
                version.status.value,
                version.updated_at.isoformat(),
                _optional_datetime(version.submitted_at),
                _optional_datetime(version.approved_at),
                _optional_datetime(version.superseded_at),
                str(version.id),
            ),
        )

    def _migrate_generated_documents(self, connection: sqlite3.Connection) -> None:
        if not self._table_exists(connection, "generated_documents"):
            return
        existing = connection.execute("SELECT COUNT(*) FROM document_versions").fetchone()
        if existing is not None and int(existing[0]) > 0:
            return

        rows = connection.execute(
            """
            SELECT * FROM generated_documents
            ORDER BY project_id ASC, document_type ASC, generated_at ASC, id ASC
            """
        ).fetchall()
        grouped: defaultdict[tuple[str, str], list[sqlite3.Row]] = defaultdict(list)
        for row in rows:
            grouped[(str(row["project_id"]), str(row["document_type"]))].append(row)

        for (project_id, document_type_value), group in grouped.items():
            document_id = str(
                uuid5(
                    NAMESPACE_URL,
                    f"tdp-document:{project_id}:{document_type_value}",
                )
            )
            first = group[0]
            latest = group[-1]
            connection.execute(
                """
                INSERT OR IGNORE INTO documents (
                    id, project_id, document_type, title, current_version_id,
                    current_approved_version_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?)
                """,
                (
                    document_id,
                    project_id,
                    document_type_value,
                    str(latest["title"]),
                    str(latest["id"]),
                    str(first["generated_at"]),
                    str(latest["generated_at"]),
                ),
            )
            for index, row in enumerate(group):
                generated_at = str(row["generated_at"])
                connection.execute(
                    """
                    INSERT OR IGNORE INTO document_versions (
                        id, document_id, project_id, source_id, target_run_id,
                        baseline_run_id, document_type, document_format,
                        version_major, version_minor, status, title, file_name,
                        content, checksum, operation_count, schema_count,
                        breaking_change_count, revision_reason, created_by,
                        created_at, updated_at, submitted_at, approved_at, superseded_at
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, 'DRAFT', ?, ?, ?, ?, ?, ?, ?,
                        ?, 'System Migration', ?, ?, NULL, NULL, NULL
                    )
                    """,
                    (
                        str(row["id"]),
                        document_id,
                        project_id,
                        str(row["source_id"]),
                        str(row["target_run_id"]),
                        (
                            str(row["baseline_run_id"])
                            if row["baseline_run_id"] is not None
                            else None
                        ),
                        document_type_value,
                        str(row["document_format"]),
                        index,
                        str(row["title"]),
                        str(row["file_name"]),
                        str(row["content"]),
                        str(row["checksum"]),
                        int(row["operation_count"]),
                        int(row["schema_count"]),
                        int(row["breaking_change_count"]),
                        "Migrated from deterministic generation history.",
                        generated_at,
                        generated_at,
                    ),
                )
                event_id = str(
                    uuid5(
                        NAMESPACE_URL,
                        f"tdp-document-migration-event:{row['id']}",
                    )
                )
                connection.execute(
                    """
                    INSERT OR IGNORE INTO document_workflow_events (
                        id, version_id, actor, action, previous_status,
                        new_status, comment, created_at
                    ) VALUES (?, ?, 'System Migration', 'GENERATED', NULL, 'DRAFT', ?, ?)
                    """,
                    (
                        event_id,
                        str(row["id"]),
                        "Migrated from deterministic generation history.",
                        generated_at,
                    ),
                )

    @staticmethod
    def _backfill_document_version_provenance(
        connection: sqlite3.Connection,
    ) -> None:
        connection.execute(
            """
            INSERT OR IGNORE INTO document_version_provenance (
                version_id, ordinal, provenance_kind,
                provenance_reference, evidence_kind, checksum
            )
            SELECT
                id, 0, 'SOURCE_REGISTRY', 'source:' || source_id, NULL, NULL
            FROM document_versions
            WHERE source_id IS NOT NULL
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO document_version_provenance (
                version_id, ordinal, provenance_kind,
                provenance_reference, evidence_kind, checksum
            )
            SELECT
                id,
                CASE WHEN source_id IS NULL THEN 0 ELSE 1 END,
                'CATALOG_SYNCHRONIZATION',
                'synchronization:' || target_run_id,
                NULL,
                NULL
            FROM document_versions
            WHERE target_run_id IS NOT NULL
            """
        )

    @staticmethod
    def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
        row = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
        return row is not None

    @staticmethod
    def _series_record(series: DocumentSeries) -> tuple[object, ...]:
        return (
            str(series.id),
            series.project_id,
            series.document_type.value,
            series.title,
            series.current_version_id,
            series.current_approved_version_id,
            series.created_at.isoformat(),
            series.updated_at.isoformat(),
        )

    @staticmethod
    def _version_record(version: DocumentVersion) -> tuple[object, ...]:
        return (
            str(version.id),
            str(version.document_id),
            version.project_id,
            version.source_id,
            version.target_run_id,
            version.baseline_run_id,
            version.document_type.value,
            version.document_format.value,
            version.version_number.major,
            version.version_number.minor,
            version.status.value,
            version.title,
            version.file_name,
            version.content,
            version.checksum,
            version.operation_count,
            version.schema_count,
            version.breaking_change_count,
            version.revision_reason,
            version.created_by,
            version.created_at.isoformat(),
            version.updated_at.isoformat(),
            _optional_datetime(version.submitted_at),
            _optional_datetime(version.approved_at),
            _optional_datetime(version.superseded_at),
        )

    @staticmethod
    def _provenance_record(
        version_id: DocumentVersionId,
        ordinal: int,
        provenance: DocumentProvenanceReference,
    ) -> tuple[object, ...]:
        return (
            str(version_id),
            ordinal,
            provenance.kind.value,
            provenance.reference,
            provenance.evidence_kind,
            provenance.checksum,
        )

    @staticmethod
    def _event_record(event: DocumentWorkflowEvent) -> tuple[object, ...]:
        return (
            str(event.id),
            str(event.version_id),
            event.actor,
            event.action.value,
            event.previous_status.value if event.previous_status is not None else None,
            event.new_status.value,
            event.comment,
            event.created_at.isoformat(),
        )

    @staticmethod
    def _series_from_row(row: sqlite3.Row) -> DocumentSeries:
        current_version_id = row["current_version_id"]
        current_approved_version_id = row["current_approved_version_id"]
        return DocumentSeries(
            id=DocumentId.from_string(str(row["id"])),
            project_id=str(row["project_id"]),
            document_type=DocumentType(str(row["document_type"])),
            title=str(row["title"]),
            current_version_id=(
                str(current_version_id) if current_version_id is not None else None
            ),
            current_approved_version_id=(
                str(current_approved_version_id)
                if current_approved_version_id is not None
                else None
            ),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )

    def _version_from_row(self, row: sqlite3.Row) -> DocumentVersion:
        source_id = row["source_id"]
        target_run_id = row["target_run_id"]
        baseline_run_id = row["baseline_run_id"]
        return DocumentVersion(
            id=DocumentVersionId.from_string(str(row["id"])),
            document_id=DocumentId.from_string(str(row["document_id"])),
            project_id=str(row["project_id"]),
            source_id=(str(source_id) if source_id is not None else None),
            target_run_id=(str(target_run_id) if target_run_id is not None else None),
            baseline_run_id=(str(baseline_run_id) if baseline_run_id is not None else None),
            document_type=DocumentType(str(row["document_type"])),
            document_format=DocumentFormat(str(row["document_format"])),
            version_number=DocumentVersionNumber(
                major=int(row["version_major"]),
                minor=int(row["version_minor"]),
            ),
            status=DocumentStatus(str(row["status"])),
            title=str(row["title"]),
            file_name=str(row["file_name"]),
            content=str(row["content"]),
            checksum=str(row["checksum"]),
            operation_count=int(row["operation_count"]),
            schema_count=int(row["schema_count"]),
            breaking_change_count=int(row["breaking_change_count"]),
            revision_reason=str(row["revision_reason"]),
            created_by=str(row["created_by"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
            submitted_at=_datetime_from_row(row["submitted_at"]),
            approved_at=_datetime_from_row(row["approved_at"]),
            superseded_at=_datetime_from_row(row["superseded_at"]),
            provenance=self._list_provenance(str(row["id"])),
        )

    def _list_provenance(
        self,
        version_id: str,
    ) -> tuple[DocumentProvenanceReference, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM document_version_provenance
                WHERE version_id = ?
                ORDER BY ordinal ASC
                """,
                (version_id,),
            ).fetchall()
        return tuple(self._provenance_from_row(row) for row in rows)

    @staticmethod
    def _provenance_from_row(
        row: sqlite3.Row,
    ) -> DocumentProvenanceReference:
        evidence_kind = row["evidence_kind"]
        checksum = row["checksum"]
        return DocumentProvenanceReference(
            kind=DocumentProvenanceKind(str(row["provenance_kind"])),
            reference=str(row["provenance_reference"]),
            evidence_kind=(str(evidence_kind) if evidence_kind is not None else None),
            checksum=str(checksum) if checksum is not None else None,
        )

    @staticmethod
    def _event_from_row(row: sqlite3.Row) -> DocumentWorkflowEvent:
        previous_status = row["previous_status"]
        return DocumentWorkflowEvent(
            id=WorkflowEventId.from_string(str(row["id"])),
            version_id=DocumentVersionId.from_string(str(row["version_id"])),
            actor=str(row["actor"]),
            action=WorkflowAction(str(row["action"])),
            previous_status=(
                DocumentStatus(str(previous_status)) if previous_status is not None else None
            ),
            new_status=DocumentStatus(str(row["new_status"])),
            comment=str(row["comment"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )


def _optional_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _datetime_from_row(value: object) -> datetime | None:
    return datetime.fromisoformat(str(value)) if value is not None else None
