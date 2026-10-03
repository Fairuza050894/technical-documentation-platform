import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import UUID

from tdp.modules.requirements.domain.errors import (
    RequirementKeyAlreadyExistsError,
    TraceLinkAlreadyExistsError,
)
from tdp.modules.requirements.domain.model import (
    RequirementId,
    RequirementKey,
    RequirementRevision,
    RequirementRevisionId,
    RequirementStatus,
    RequirementType,
    TraceLink,
    TraceRelation,
    TraceTargetType,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS requirement_revisions (
    revision_id TEXT PRIMARY KEY,
    requirement_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    requirement_key TEXT NOT NULL,
    revision INTEGER NOT NULL,
    requirement_type TEXT NOT NULL,
    status TEXT NOT NULL,
    title TEXT NOT NULL,
    statement TEXT NOT NULL,
    owner TEXT NOT NULL,
    feature_id TEXT,
    acceptance_criteria_json TEXT NOT NULL,
    changed_by TEXT NOT NULL,
    change_reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(requirement_id, revision),
    UNIQUE(project_id, requirement_key, revision),
    FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE INDEX IF NOT EXISTS idx_requirement_revisions_project
ON requirement_revisions(project_id, requirement_key, revision DESC);

CREATE TABLE IF NOT EXISTS requirement_trace_links (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    requirement_revision_id TEXT NOT NULL,
    target_type TEXT NOT NULL,
    relation TEXT NOT NULL,
    target_reference TEXT NOT NULL,
    verified INTEGER NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(requirement_revision_id, target_type, relation, target_reference),
    FOREIGN KEY(requirement_revision_id) REFERENCES requirement_revisions(revision_id)
);

CREATE INDEX IF NOT EXISTS idx_requirement_trace_revision
ON requirement_trace_links(requirement_revision_id, target_type, relation);
"""


class SqliteRequirementRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    async def add_revision(
        self,
        revision: RequirementRevision,
        trace_links: tuple[TraceLink, ...] = (),
    ) -> None:
        try:
            await asyncio.to_thread(self._add_revision, revision, trace_links)
        except sqlite3.IntegrityError as exc:
            raise RequirementKeyAlreadyExistsError(
                f"Requirement revision {revision.key} r{revision.revision} already exists."
            ) from exc

    async def get_latest(
        self,
        project_id: str,
        requirement_id: RequirementId,
    ) -> RequirementRevision | None:
        return await asyncio.to_thread(self._get_latest, project_id, requirement_id)

    async def get_latest_by_key(
        self,
        project_id: str,
        key: RequirementKey,
    ) -> RequirementRevision | None:
        return await asyncio.to_thread(self._get_latest_by_key, project_id, key)

    async def list_latest_by_project(self, project_id: str) -> list[RequirementRevision]:
        return await asyncio.to_thread(self._list_latest_by_project, project_id)

    async def list_revisions(
        self,
        project_id: str,
        requirement_id: RequirementId,
    ) -> list[RequirementRevision]:
        return await asyncio.to_thread(self._list_revisions, project_id, requirement_id)

    async def add_trace_link(self, link: TraceLink) -> None:
        try:
            await asyncio.to_thread(self._add_trace_link, link)
        except sqlite3.IntegrityError as exc:
            raise TraceLinkAlreadyExistsError(
                "The same verified trace link is already registered for this requirement revision."
            ) from exc

    async def list_trace_links(
        self,
        requirement_revision_id: RequirementRevisionId,
    ) -> list[TraceLink]:
        return await asyncio.to_thread(self._list_trace_links, requirement_revision_id)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(_SCHEMA)

    def _add_revision(
        self,
        revision: RequirementRevision,
        trace_links: tuple[TraceLink, ...],
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO requirement_revisions (
                    revision_id, requirement_id, project_id, requirement_key, revision,
                    requirement_type, status, title, statement, owner, feature_id,
                    acceptance_criteria_json, changed_by, change_reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(revision.revision_id),
                    str(revision.requirement_id),
                    revision.project_id,
                    str(revision.key),
                    revision.revision,
                    revision.requirement_type.value,
                    revision.status.value,
                    revision.title,
                    revision.statement,
                    revision.owner,
                    revision.feature_id,
                    json.dumps(revision.acceptance_criteria, separators=(",", ":")),
                    revision.changed_by,
                    revision.change_reason,
                    revision.created_at.isoformat(),
                ),
            )
            for link in trace_links:
                self._insert_trace_link(connection, link)

    def _get_latest(
        self,
        project_id: str,
        requirement_id: RequirementId,
    ) -> RequirementRevision | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM requirement_revisions
                WHERE project_id = ? AND requirement_id = ?
                ORDER BY revision DESC
                LIMIT 1
                """,
                (project_id, str(requirement_id)),
            ).fetchone()
        return self._revision_from_row(row) if row is not None else None

    def _get_latest_by_key(
        self,
        project_id: str,
        key: RequirementKey,
    ) -> RequirementRevision | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM requirement_revisions
                WHERE project_id = ? AND requirement_key = ?
                ORDER BY revision DESC
                LIMIT 1
                """,
                (project_id, str(key)),
            ).fetchone()
        return self._revision_from_row(row) if row is not None else None

    def _list_latest_by_project(self, project_id: str) -> list[RequirementRevision]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT current.*
                FROM requirement_revisions AS current
                JOIN (
                    SELECT requirement_id, MAX(revision) AS latest_revision
                    FROM requirement_revisions
                    WHERE project_id = ?
                    GROUP BY requirement_id
                ) AS latest
                  ON latest.requirement_id = current.requirement_id
                 AND latest.latest_revision = current.revision
                WHERE current.project_id = ?
                ORDER BY current.requirement_key ASC, current.requirement_id ASC
                """,
                (project_id, project_id),
            ).fetchall()
        return [self._revision_from_row(row) for row in rows]

    def _list_revisions(
        self,
        project_id: str,
        requirement_id: RequirementId,
    ) -> list[RequirementRevision]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM requirement_revisions
                WHERE project_id = ? AND requirement_id = ?
                ORDER BY revision ASC
                """,
                (project_id, str(requirement_id)),
            ).fetchall()
        return [self._revision_from_row(row) for row in rows]

    def _add_trace_link(self, link: TraceLink) -> None:
        with self._connect() as connection:
            self._insert_trace_link(connection, link)

    @staticmethod
    def _insert_trace_link(connection: sqlite3.Connection, link: TraceLink) -> None:
        connection.execute(
            """
            INSERT INTO requirement_trace_links (
                id, project_id, requirement_revision_id, target_type, relation,
                target_reference, verified, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(link.id),
                link.project_id,
                str(link.requirement_revision_id),
                link.target_type.value,
                link.relation.value,
                link.target_reference,
                int(link.verified),
                link.created_by,
                link.created_at.isoformat(),
            ),
        )

    def _list_trace_links(
        self,
        requirement_revision_id: RequirementRevisionId,
    ) -> list[TraceLink]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM requirement_trace_links
                WHERE requirement_revision_id = ?
                ORDER BY target_type ASC, relation ASC, target_reference ASC
                """,
                (str(requirement_revision_id),),
            ).fetchall()
        return [self._trace_from_row(row) for row in rows]

    @staticmethod
    def _revision_from_row(row: sqlite3.Row) -> RequirementRevision:
        criteria_raw = json.loads(str(row["acceptance_criteria_json"]))
        criteria = tuple(str(item) for item in criteria_raw)
        return RequirementRevision(
            revision_id=RequirementRevisionId.from_string(str(row["revision_id"])),
            requirement_id=RequirementId.from_string(str(row["requirement_id"])),
            project_id=str(row["project_id"]),
            key=RequirementKey(str(row["requirement_key"])),
            revision=int(row["revision"]),
            requirement_type=RequirementType(str(row["requirement_type"])),
            status=RequirementStatus(str(row["status"])),
            title=str(row["title"]),
            statement=str(row["statement"]),
            owner=str(row["owner"]),
            feature_id=str(row["feature_id"]) if row["feature_id"] is not None else None,
            acceptance_criteria=criteria,
            changed_by=str(row["changed_by"]),
            change_reason=str(row["change_reason"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )

    @staticmethod
    def _trace_from_row(row: sqlite3.Row) -> TraceLink:
        return TraceLink(
            id=UUID(str(row["id"])),
            project_id=str(row["project_id"]),
            requirement_revision_id=RequirementRevisionId.from_string(
                str(row["requirement_revision_id"])
            ),
            target_type=TraceTargetType(str(row["target_type"])),
            relation=TraceRelation(str(row["relation"])),
            target_reference=str(row["target_reference"]),
            verified=bool(row["verified"]),
            created_by=str(row["created_by"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )
