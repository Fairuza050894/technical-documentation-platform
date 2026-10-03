import sqlite3
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from tdp.modules.governance.domain.model import (
    ChangeSurface,
    ImpactAssessment,
    ImpactTarget,
    RequirementRevision,
    RequirementStatus,
    RequirementType,
    TraceLink,
    TraceTargetType,
    WorkflowCase,
    WorkflowState,
)


class SqliteGovernanceRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS governance_requirement_revisions (
                    id TEXT PRIMARY KEY,
                    requirement_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    requirement_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    title TEXT NOT NULL,
                    statement TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(requirement_id, revision)
                );
                CREATE INDEX IF NOT EXISTS idx_governance_requirement_project
                    ON governance_requirement_revisions(project_id, requirement_id, revision);

                CREATE TABLE IF NOT EXISTS governance_trace_links (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    requirement_id TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(project_id, requirement_id, target_type, target_id, relation)
                );
                CREATE INDEX IF NOT EXISTS idx_governance_trace_project
                    ON governance_trace_links(project_id, requirement_id);

                CREATE TABLE IF NOT EXISTS governance_impact_assessments (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    change_reference TEXT NOT NULL,
                    surface TEXT NOT NULL,
                    affected_targets TEXT NOT NULL,
                    requires_action INTEGER NOT NULL,
                    assessed_by TEXT NOT NULL,
                    assessed_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_governance_impact_project
                    ON governance_impact_assessments(project_id, assessed_at);

                CREATE TABLE IF NOT EXISTS governance_workflow_cases (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    impact_assessment_id TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_governance_workflow_project
                    ON governance_workflow_cases(project_id, state, updated_at);

                CREATE TABLE IF NOT EXISTS governance_workflow_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT NOT NULL,
                    from_state TEXT NOT NULL,
                    to_state TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    comment TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def add_requirement(self, revision: RequirementRevision) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO governance_requirement_revisions (
                    id, requirement_id, project_id, revision, requirement_type, status,
                    title, statement, rationale, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    revision.id,
                    revision.requirement_id,
                    revision.project_id,
                    revision.revision,
                    revision.requirement_type.value,
                    revision.status.value,
                    revision.title,
                    revision.statement,
                    revision.rationale,
                    revision.created_by,
                    revision.created_at.isoformat(),
                ),
            )

    def latest_requirement(self, requirement_id: str) -> RequirementRevision | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM governance_requirement_revisions
                WHERE requirement_id = ? ORDER BY revision DESC LIMIT 1
                """,
                (requirement_id,),
            ).fetchone()
        return self._requirement_from_row(row) if row is not None else None

    def list_requirements(self, project_id: str) -> list[RequirementRevision]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT current.*
                FROM governance_requirement_revisions current
                JOIN (
                    SELECT requirement_id, MAX(revision) AS latest_revision
                    FROM governance_requirement_revisions
                    WHERE project_id = ?
                    GROUP BY requirement_id
                ) latest
                ON current.requirement_id = latest.requirement_id
                AND current.revision = latest.latest_revision
                ORDER BY current.created_at ASC
                """,
                (project_id,),
            ).fetchall()
        return [self._requirement_from_row(row) for row in rows]

    def add_trace_link(self, link: TraceLink) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO governance_trace_links (
                    id, project_id, requirement_id, target_type, target_id,
                    relation, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    link.id,
                    link.project_id,
                    link.requirement_id,
                    link.target_type.value,
                    link.target_id,
                    link.relation,
                    link.created_by,
                    link.created_at.isoformat(),
                ),
            )

    def list_trace_links(self, project_id: str) -> list[TraceLink]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM governance_trace_links WHERE project_id = ? ORDER BY created_at ASC",
                (project_id,),
            ).fetchall()
        return [self._trace_from_row(row) for row in rows]

    def add_impact(self, assessment: ImpactAssessment) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO governance_impact_assessments (
                    id, project_id, change_reference, surface, affected_targets,
                    requires_action, assessed_by, assessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    assessment.id,
                    assessment.project_id,
                    assessment.change_reference,
                    assessment.surface.value,
                    ",".join(target.value for target in assessment.affected_targets),
                    int(assessment.requires_action),
                    assessment.assessed_by,
                    assessment.assessed_at.isoformat(),
                ),
            )

    def get_impact(self, assessment_id: str) -> ImpactAssessment | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM governance_impact_assessments WHERE id = ?",
                (assessment_id,),
            ).fetchone()
        return self._impact_from_row(row) if row is not None else None

    def list_impacts(self, project_id: str) -> list[ImpactAssessment]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM governance_impact_assessments
                WHERE project_id = ? ORDER BY assessed_at DESC
                """,
                (project_id,),
            ).fetchall()
        return [self._impact_from_row(row) for row in rows]

    def add_workflow_case(self, case: WorkflowCase) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO governance_workflow_cases (
                    id, project_id, impact_assessment_id, owner, state,
                    created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case.id,
                    case.project_id,
                    case.impact_assessment_id,
                    case.owner,
                    case.state.value,
                    case.created_by,
                    case.created_at.isoformat(),
                    case.updated_at.isoformat(),
                ),
            )

    def get_workflow_case(self, case_id: str) -> WorkflowCase | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM governance_workflow_cases WHERE id = ?",
                (case_id,),
            ).fetchone()
        return self._workflow_from_row(row) if row is not None else None

    def update_workflow_case(
        self,
        case: WorkflowCase,
        *,
        previous_state: WorkflowState,
        actor: str,
        comment: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE governance_workflow_cases SET state = ?, updated_at = ? WHERE id = ?",
                (case.state.value, case.updated_at.isoformat(), case.id),
            )
            connection.execute(
                """
                INSERT INTO governance_workflow_events (
                    case_id, from_state, to_state, actor, comment, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    case.id,
                    previous_state.value,
                    case.state.value,
                    actor,
                    comment,
                    case.updated_at.isoformat(),
                ),
            )

    def list_workflow_cases(self, project_id: str) -> list[WorkflowCase]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM governance_workflow_cases
                WHERE project_id = ? ORDER BY updated_at DESC
                """,
                (project_id,),
            ).fetchall()
        return [self._workflow_from_row(row) for row in rows]

    @staticmethod
    def _requirement_from_row(row: sqlite3.Row) -> RequirementRevision:
        return RequirementRevision(
            id=row["id"],
            requirement_id=row["requirement_id"],
            project_id=row["project_id"],
            revision=int(row["revision"]),
            requirement_type=RequirementType(row["requirement_type"]),
            status=RequirementStatus(row["status"]),
            title=row["title"],
            statement=row["statement"],
            rationale=row["rationale"],
            created_by=row["created_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    @staticmethod
    def _trace_from_row(row: sqlite3.Row) -> TraceLink:
        return TraceLink(
            id=row["id"],
            project_id=row["project_id"],
            requirement_id=row["requirement_id"],
            target_type=TraceTargetType(row["target_type"]),
            target_id=row["target_id"],
            relation=row["relation"],
            created_by=row["created_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    @staticmethod
    def _impact_from_row(row: sqlite3.Row) -> ImpactAssessment:
        targets = tuple(
            ImpactTarget(value)
            for value in str(row["affected_targets"]).split(",")
            if value
        )
        return ImpactAssessment(
            id=row["id"],
            project_id=row["project_id"],
            change_reference=row["change_reference"],
            surface=ChangeSurface(row["surface"]),
            affected_targets=targets,
            requires_action=bool(row["requires_action"]),
            assessed_by=row["assessed_by"],
            assessed_at=datetime.fromisoformat(row["assessed_at"]),
        )

    @staticmethod
    def _workflow_from_row(row: sqlite3.Row) -> WorkflowCase:
        return WorkflowCase(
            id=row["id"],
            project_id=row["project_id"],
            impact_assessment_id=row["impact_assessment_id"],
            owner=row["owner"],
            state=WorkflowState(row["state"]),
            created_by=row["created_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


def requirement_coverage(
    requirements: Iterable[RequirementRevision],
    trace_links: Iterable[TraceLink],
) -> tuple[int, int, int]:
    requirement_ids = {item.requirement_id for item in requirements}
    linked_ids = {item.requirement_id for item in trace_links if item.requirement_id in requirement_ids}
    total = len(requirement_ids)
    linked = len(linked_ids)
    coverage = round((linked / total) * 100) if total else 0
    return total, linked, coverage
