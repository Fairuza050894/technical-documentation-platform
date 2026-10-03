import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from tdp.modules.governance.domain.errors import RequirementKeyAlreadyExistsError
from tdp.modules.governance.domain.model import (
    ImpactAssessment,
    ImpactSeverity,
    RequirementKind,
    RequirementRevision,
    RequirementStatus,
    TraceLink,
    TraceRelation,
    TraceTargetType,
    WorkflowAction,
    WorkflowEvent,
    WorkflowState,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS requirement_revisions (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    requirement_key TEXT NOT NULL,
    revision INTEGER NOT NULL,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    statement TEXT NOT NULL,
    acceptance_criteria TEXT NOT NULL,
    owner TEXT NOT NULL,
    status TEXT NOT NULL,
    previous_revision_id TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(project_id, requirement_key, revision)
);
CREATE INDEX IF NOT EXISTS idx_requirement_revisions_project_key
ON requirement_revisions(project_id, requirement_key, revision DESC);

CREATE TABLE IF NOT EXISTS requirement_trace_links (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    requirement_revision_id TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    rationale TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(requirement_revision_id, target_type, target_id, relation)
);
CREATE INDEX IF NOT EXISTS idx_requirement_trace_target
ON requirement_trace_links(project_id, target_type, target_id);

CREATE TABLE IF NOT EXISTS impact_assessments (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    change_reference TEXT NOT NULL,
    changed_target_type TEXT NOT NULL,
    changed_target_id TEXT NOT NULL,
    severity TEXT NOT NULL,
    impacted_requirement_ids TEXT NOT NULL,
    required_actions TEXT NOT NULL,
    workflow_state TEXT NOT NULL,
    rationale TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_impact_assessments_project
ON impact_assessments(project_id, created_at DESC);

CREATE TABLE IF NOT EXISTS impact_workflow_events (
    id TEXT PRIMARY KEY,
    assessment_id TEXT NOT NULL,
    action TEXT NOT NULL,
    previous_state TEXT NOT NULL,
    new_state TEXT NOT NULL,
    actor TEXT NOT NULL,
    comment TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_impact_workflow_events_assessment
ON impact_workflow_events(assessment_id, created_at ASC);
"""


class SqliteGovernanceRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    async def add_requirement(self, revision: RequirementRevision) -> None:
        try:
            await asyncio.to_thread(self._insert_requirement, revision)
        except sqlite3.IntegrityError as exc:
            raise RequirementKeyAlreadyExistsError(
                f"Requirement {revision.key} revision {revision.revision} already exists."
            ) from exc

    async def add_revision(self, revision: RequirementRevision) -> None:
        await self.add_requirement(revision)

    async def get_requirement_revision(self, revision_id: str) -> RequirementRevision | None:
        return await asyncio.to_thread(self._get_requirement_revision, revision_id)

    async def get_latest_requirement(self, project_id: str, key: str) -> RequirementRevision | None:
        return await asyncio.to_thread(self._get_latest_requirement, project_id, key)

    async def list_latest_requirements(self, project_id: str) -> list[RequirementRevision]:
        return await asyncio.to_thread(self._list_latest_requirements, project_id)

    async def add_trace_link(self, link: TraceLink) -> None:
        await asyncio.to_thread(self._insert_trace_link, link)

    async def list_trace_links(self, project_id: str) -> list[TraceLink]:
        return await asyncio.to_thread(self._list_trace_links, project_id)

    async def list_trace_links_for_target(
        self,
        project_id: str,
        target_type: str,
        target_id: str,
    ) -> list[TraceLink]:
        return await asyncio.to_thread(
            self._list_trace_links_for_target,
            project_id,
            target_type,
            target_id,
        )

    async def add_impact_assessment(self, assessment: ImpactAssessment) -> None:
        await asyncio.to_thread(self._insert_impact_assessment, assessment)

    async def update_impact_assessment(self, assessment: ImpactAssessment) -> None:
        await asyncio.to_thread(self._update_impact_assessment, assessment)

    async def get_impact_assessment(self, assessment_id: str) -> ImpactAssessment | None:
        return await asyncio.to_thread(self._get_impact_assessment, assessment_id)

    async def list_impact_assessments(self, project_id: str) -> list[ImpactAssessment]:
        return await asyncio.to_thread(self._list_impact_assessments, project_id)

    async def add_workflow_event(self, event: WorkflowEvent) -> None:
        await asyncio.to_thread(self._insert_workflow_event, event)

    async def list_workflow_events(self, assessment_id: str) -> list[WorkflowEvent]:
        return await asyncio.to_thread(self._list_workflow_events, assessment_id)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(_SCHEMA)

    def _insert_requirement(self, revision: RequirementRevision) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO requirement_revisions (
                    id, workspace_id, project_id, requirement_key, revision, kind,
                    title, statement, acceptance_criteria, owner, status,
                    previous_revision_id, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    revision.id,
                    revision.workspace_id,
                    revision.project_id,
                    revision.key,
                    revision.revision,
                    revision.kind.value,
                    revision.title,
                    revision.statement,
                    json.dumps(revision.acceptance_criteria),
                    revision.owner,
                    revision.status.value,
                    revision.previous_revision_id,
                    revision.created_by,
                    revision.created_at.isoformat(),
                ),
            )

    def _get_requirement_revision(self, revision_id: str) -> RequirementRevision | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM requirement_revisions WHERE id = ?",
                (revision_id,),
            ).fetchone()
        return self._requirement_from_row(row) if row is not None else None

    def _get_latest_requirement(self, project_id: str, key: str) -> RequirementRevision | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM requirement_revisions
                WHERE project_id = ? AND requirement_key = ?
                ORDER BY revision DESC LIMIT 1
                """,
                (project_id, key),
            ).fetchone()
        return self._requirement_from_row(row) if row is not None else None

    def _list_latest_requirements(self, project_id: str) -> list[RequirementRevision]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT r.* FROM requirement_revisions r
                JOIN (
                    SELECT requirement_key, MAX(revision) AS max_revision
                    FROM requirement_revisions
                    WHERE project_id = ?
                    GROUP BY requirement_key
                ) latest
                  ON latest.requirement_key = r.requirement_key
                 AND latest.max_revision = r.revision
                WHERE r.project_id = ?
                ORDER BY r.requirement_key ASC
                """,
                (project_id, project_id),
            ).fetchall()
        return [self._requirement_from_row(row) for row in rows]

    def _insert_trace_link(self, link: TraceLink) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO requirement_trace_links (
                    id, workspace_id, project_id, requirement_revision_id,
                    target_type, target_id, relation, rationale, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    link.id,
                    link.workspace_id,
                    link.project_id,
                    link.requirement_revision_id,
                    link.target_type.value,
                    link.target_id,
                    link.relation.value,
                    link.rationale,
                    link.created_by,
                    link.created_at.isoformat(),
                ),
            )

    def _list_trace_links(self, project_id: str) -> list[TraceLink]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM requirement_trace_links
                WHERE project_id = ?
                ORDER BY created_at ASC, id ASC
                """,
                (project_id,),
            ).fetchall()
        return [self._trace_link_from_row(row) for row in rows]

    def _list_trace_links_for_target(
        self,
        project_id: str,
        target_type: str,
        target_id: str,
    ) -> list[TraceLink]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM requirement_trace_links
                WHERE project_id = ? AND target_type = ? AND target_id = ?
                ORDER BY created_at ASC, id ASC
                """,
                (project_id, target_type, target_id),
            ).fetchall()
        return [self._trace_link_from_row(row) for row in rows]

    def _insert_impact_assessment(self, assessment: ImpactAssessment) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO impact_assessments (
                    id, workspace_id, project_id, change_reference,
                    changed_target_type, changed_target_id, severity,
                    impacted_requirement_ids, required_actions, workflow_state,
                    rationale, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._impact_record(assessment),
            )

    def _update_impact_assessment(self, assessment: ImpactAssessment) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE impact_assessments
                SET severity = ?, impacted_requirement_ids = ?, required_actions = ?,
                    workflow_state = ?, rationale = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    assessment.severity.value,
                    json.dumps(assessment.impacted_requirement_ids),
                    json.dumps(assessment.required_actions),
                    assessment.workflow_state.value,
                    assessment.rationale,
                    assessment.updated_at.isoformat(),
                    assessment.id,
                ),
            )

    def _get_impact_assessment(self, assessment_id: str) -> ImpactAssessment | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM impact_assessments WHERE id = ?",
                (assessment_id,),
            ).fetchone()
        return self._impact_from_row(row) if row is not None else None

    def _list_impact_assessments(self, project_id: str) -> list[ImpactAssessment]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM impact_assessments
                WHERE project_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (project_id,),
            ).fetchall()
        return [self._impact_from_row(row) for row in rows]

    def _insert_workflow_event(self, event: WorkflowEvent) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO impact_workflow_events (
                    id, assessment_id, action, previous_state, new_state,
                    actor, comment, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.assessment_id,
                    event.action.value,
                    event.previous_state.value,
                    event.new_state.value,
                    event.actor,
                    event.comment,
                    event.created_at.isoformat(),
                ),
            )

    def _list_workflow_events(self, assessment_id: str) -> list[WorkflowEvent]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM impact_workflow_events
                WHERE assessment_id = ?
                ORDER BY created_at ASC, id ASC
                """,
                (assessment_id,),
            ).fetchall()
        return [self._workflow_event_from_row(row) for row in rows]

    @staticmethod
    def _impact_record(assessment: ImpactAssessment) -> tuple[object, ...]:
        return (
            assessment.id,
            assessment.workspace_id,
            assessment.project_id,
            assessment.change_reference,
            assessment.changed_target_type.value,
            assessment.changed_target_id,
            assessment.severity.value,
            json.dumps(assessment.impacted_requirement_ids),
            json.dumps(assessment.required_actions),
            assessment.workflow_state.value,
            assessment.rationale,
            assessment.created_by,
            assessment.created_at.isoformat(),
            assessment.updated_at.isoformat(),
        )

    @staticmethod
    def _requirement_from_row(row: sqlite3.Row) -> RequirementRevision:
        return RequirementRevision(
            id=str(row["id"]),
            workspace_id=str(row["workspace_id"]),
            project_id=str(row["project_id"]),
            key=str(row["requirement_key"]),
            revision=int(row["revision"]),
            kind=RequirementKind(str(row["kind"])),
            title=str(row["title"]),
            statement=str(row["statement"]),
            acceptance_criteria=tuple(json.loads(str(row["acceptance_criteria"]))),
            owner=str(row["owner"]),
            status=RequirementStatus(str(row["status"])),
            previous_revision_id=(
                str(row["previous_revision_id"])
                if row["previous_revision_id"] is not None
                else None
            ),
            created_by=str(row["created_by"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )

    @staticmethod
    def _trace_link_from_row(row: sqlite3.Row) -> TraceLink:
        return TraceLink(
            id=str(row["id"]),
            workspace_id=str(row["workspace_id"]),
            project_id=str(row["project_id"]),
            requirement_revision_id=str(row["requirement_revision_id"]),
            target_type=TraceTargetType(str(row["target_type"])),
            target_id=str(row["target_id"]),
            relation=TraceRelation(str(row["relation"])),
            rationale=str(row["rationale"]),
            created_by=str(row["created_by"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )

    @staticmethod
    def _impact_from_row(row: sqlite3.Row) -> ImpactAssessment:
        return ImpactAssessment(
            id=str(row["id"]),
            workspace_id=str(row["workspace_id"]),
            project_id=str(row["project_id"]),
            change_reference=str(row["change_reference"]),
            changed_target_type=TraceTargetType(str(row["changed_target_type"])),
            changed_target_id=str(row["changed_target_id"]),
            severity=ImpactSeverity(str(row["severity"])),
            impacted_requirement_ids=tuple(json.loads(str(row["impacted_requirement_ids"]))),
            required_actions=tuple(json.loads(str(row["required_actions"]))),
            workflow_state=WorkflowState(str(row["workflow_state"])),
            rationale=str(row["rationale"]),
            created_by=str(row["created_by"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )

    @staticmethod
    def _workflow_event_from_row(row: sqlite3.Row) -> WorkflowEvent:
        return WorkflowEvent(
            id=str(row["id"]),
            assessment_id=str(row["assessment_id"]),
            action=WorkflowAction(str(row["action"])),
            previous_state=WorkflowState(str(row["previous_state"])),
            new_state=WorkflowState(str(row["new_state"])),
            actor=str(row["actor"]),
            comment=str(row["comment"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )
