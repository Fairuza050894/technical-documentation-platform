import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from tdp.modules.requirements.domain.errors import (
    RequirementKeyAlreadyExistsError,
    TraceabilityLinkAlreadyExistsError,
)
from tdp.modules.requirements.domain.model import (
    Requirement,
    RequirementId,
    RequirementRevision,
    RequirementStatus,
    RequirementType,
    TraceabilityLink,
    TraceabilityLinkId,
    TraceabilityRelation,
    TraceabilityTargetType,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS requirements (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    requirement_key TEXT NOT NULL,
    requirement_type TEXT NOT NULL,
    title TEXT NOT NULL,
    statement TEXT NOT NULL,
    acceptance_criteria_json TEXT NOT NULL,
    rationale TEXT NOT NULL,
    feature_id TEXT,
    status TEXT NOT NULL,
    revision INTEGER NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, requirement_key),
    FOREIGN KEY(project_id) REFERENCES projects(id),
    FOREIGN KEY(feature_id) REFERENCES features(id)
);

CREATE INDEX IF NOT EXISTS idx_requirements_project_status
ON requirements(project_id, status, requirement_key);

CREATE TABLE IF NOT EXISTS requirement_revisions (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    requirement_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    title TEXT NOT NULL,
    statement TEXT NOT NULL,
    acceptance_criteria_json TEXT NOT NULL,
    rationale TEXT NOT NULL,
    feature_id TEXT,
    status TEXT NOT NULL,
    actor TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY(requirement_id) REFERENCES requirements(id)
);

CREATE INDEX IF NOT EXISTS idx_requirement_revisions_requirement
ON requirement_revisions(requirement_id, event_id ASC);

CREATE TABLE IF NOT EXISTS requirement_traceability_links (
    id TEXT PRIMARY KEY,
    requirement_id TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(requirement_id, target_type, target_id, relation),
    FOREIGN KEY(requirement_id) REFERENCES requirements(id)
);

CREATE INDEX IF NOT EXISTS idx_requirement_links_requirement
ON requirement_traceability_links(requirement_id, target_type, relation);
"""


class SqliteRequirementRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    async def add(self, requirement: Requirement, revision: RequirementRevision) -> None:
        try:
            await asyncio.to_thread(self._add, requirement, revision)
        except sqlite3.IntegrityError as exc:
            raise RequirementKeyAlreadyExistsError(
                f"Requirement key {requirement.key} already exists in project {requirement.project_id}."
            ) from exc

    async def update(self, requirement: Requirement, revision: RequirementRevision) -> None:
        await asyncio.to_thread(self._update, requirement, revision)

    async def get(self, requirement_id: RequirementId) -> Requirement | None:
        return await asyncio.to_thread(self._get, requirement_id)

    async def get_by_project_key(self, project_id: str, key: str) -> Requirement | None:
        return await asyncio.to_thread(self._get_by_project_key, project_id, key)

    async def list_by_project(self, project_id: str) -> list[Requirement]:
        return await asyncio.to_thread(self._list_by_project, project_id)

    async def list_revisions(self, requirement_id: RequirementId) -> list[RequirementRevision]:
        return await asyncio.to_thread(self._list_revisions, requirement_id)

    async def add_link(self, link: TraceabilityLink) -> None:
        try:
            await asyncio.to_thread(self._add_link, link)
        except sqlite3.IntegrityError as exc:
            raise TraceabilityLinkAlreadyExistsError(
                "This traceability relationship already exists."
            ) from exc

    async def list_links(self, requirement_id: RequirementId) -> list[TraceabilityLink]:
        return await asyncio.to_thread(self._list_links, requirement_id)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(_SCHEMA)

    def _add(self, requirement: Requirement, revision: RequirementRevision) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO requirements (
                    id, workspace_id, project_id, requirement_key, requirement_type,
                    title, statement, acceptance_criteria_json, rationale, feature_id,
                    status, revision, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._requirement_record(requirement),
            )
            self._insert_revision(connection, revision)

    def _update(self, requirement: Requirement, revision: RequirementRevision) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE requirements
                SET requirement_type = ?, title = ?, statement = ?,
                    acceptance_criteria_json = ?, rationale = ?, feature_id = ?,
                    status = ?, revision = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    requirement.requirement_type.value,
                    requirement.title,
                    requirement.statement,
                    json.dumps(requirement.acceptance_criteria),
                    requirement.rationale,
                    requirement.feature_id,
                    requirement.status.value,
                    requirement.revision,
                    requirement.updated_at.isoformat(),
                    str(requirement.id),
                ),
            )
            self._insert_revision(connection, revision)

    def _get(self, requirement_id: RequirementId) -> Requirement | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM requirements WHERE id = ?",
                (str(requirement_id),),
            ).fetchone()
        return self._requirement_from_row(row) if row is not None else None

    def _get_by_project_key(self, project_id: str, key: str) -> Requirement | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM requirements WHERE project_id = ? AND requirement_key = ?",
                (project_id, key),
            ).fetchone()
        return self._requirement_from_row(row) if row is not None else None

    def _list_by_project(self, project_id: str) -> list[Requirement]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM requirements
                WHERE project_id = ?
                ORDER BY CASE status
                    WHEN 'DRAFT' THEN 0
                    WHEN 'APPROVED' THEN 1
                    ELSE 2 END,
                    requirement_key ASC
                """,
                (project_id,),
            ).fetchall()
        return [self._requirement_from_row(row) for row in rows]

    def _list_revisions(self, requirement_id: RequirementId) -> list[RequirementRevision]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM requirement_revisions
                WHERE requirement_id = ?
                ORDER BY event_id ASC
                """,
                (str(requirement_id),),
            ).fetchall()
        return [self._revision_from_row(row) for row in rows]

    def _add_link(self, link: TraceabilityLink) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO requirement_traceability_links (
                    id, requirement_id, target_type, target_id, relation,
                    created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(link.id),
                    str(link.requirement_id),
                    link.target_type.value,
                    link.target_id,
                    link.relation.value,
                    link.created_by,
                    link.created_at.isoformat(),
                ),
            )

    def _list_links(self, requirement_id: RequirementId) -> list[TraceabilityLink]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM requirement_traceability_links
                WHERE requirement_id = ?
                ORDER BY target_type ASC, relation ASC, created_at ASC, id ASC
                """,
                (str(requirement_id),),
            ).fetchall()
        return [self._link_from_row(row) for row in rows]

    @staticmethod
    def _insert_revision(
        connection: sqlite3.Connection,
        revision: RequirementRevision,
    ) -> None:
        connection.execute(
            """
            INSERT INTO requirement_revisions (
                requirement_id, revision, title, statement, acceptance_criteria_json,
                rationale, feature_id, status, actor, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(revision.requirement_id),
                revision.revision,
                revision.title,
                revision.statement,
                json.dumps(revision.acceptance_criteria),
                revision.rationale,
                revision.feature_id,
                revision.status.value,
                revision.actor,
                revision.recorded_at.isoformat(),
            ),
        )

    @staticmethod
    def _requirement_record(requirement: Requirement) -> tuple[object, ...]:
        return (
            str(requirement.id),
            requirement.workspace_id,
            requirement.project_id,
            requirement.key,
            requirement.requirement_type.value,
            requirement.title,
            requirement.statement,
            json.dumps(requirement.acceptance_criteria),
            requirement.rationale,
            requirement.feature_id,
            requirement.status.value,
            requirement.revision,
            requirement.created_by,
            requirement.created_at.isoformat(),
            requirement.updated_at.isoformat(),
        )

    @staticmethod
    def _requirement_from_row(row: sqlite3.Row) -> Requirement:
        criteria = tuple(str(item) for item in json.loads(str(row["acceptance_criteria_json"])))
        return Requirement(
            id=RequirementId.from_string(str(row["id"])),
            workspace_id=str(row["workspace_id"]),
            project_id=str(row["project_id"]),
            key=str(row["requirement_key"]),
            requirement_type=RequirementType(str(row["requirement_type"])),
            title=str(row["title"]),
            statement=str(row["statement"]),
            acceptance_criteria=criteria,
            rationale=str(row["rationale"]),
            feature_id=str(row["feature_id"]) if row["feature_id"] is not None else None,
            status=RequirementStatus(str(row["status"])),
            revision=int(row["revision"]),
            created_by=str(row["created_by"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )

    @staticmethod
    def _revision_from_row(row: sqlite3.Row) -> RequirementRevision:
        criteria = tuple(str(item) for item in json.loads(str(row["acceptance_criteria_json"])))
        return RequirementRevision(
            requirement_id=RequirementId.from_string(str(row["requirement_id"])),
            revision=int(row["revision"]),
            title=str(row["title"]),
            statement=str(row["statement"]),
            acceptance_criteria=criteria,
            rationale=str(row["rationale"]),
            feature_id=str(row["feature_id"]) if row["feature_id"] is not None else None,
            status=RequirementStatus(str(row["status"])),
            actor=str(row["actor"]),
            recorded_at=datetime.fromisoformat(str(row["recorded_at"])),
        )

    @staticmethod
    def _link_from_row(row: sqlite3.Row) -> TraceabilityLink:
        return TraceabilityLink(
            id=TraceabilityLinkId.from_string(str(row["id"])),
            requirement_id=RequirementId.from_string(str(row["requirement_id"])),
            target_type=TraceabilityTargetType(str(row["target_type"])),
            target_id=str(row["target_id"]),
            relation=TraceabilityRelation(str(row["relation"])),
            created_by=str(row["created_by"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )
