import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path

from tdp.modules.workflow.domain.model import (
    WorkflowAction,
    WorkflowEntityType,
    WorkflowEvent,
    WorkflowEventId,
    WorkflowItem,
    WorkflowItemId,
    WorkflowPriority,
    WorkflowState,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS workflow_items (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    title TEXT NOT NULL,
    priority TEXT NOT NULL,
    state TEXT NOT NULL,
    assignee TEXT NOT NULL,
    created_by TEXT NOT NULL,
    due_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE INDEX IF NOT EXISTS idx_workflow_items_project_state
ON workflow_items(project_id, state, priority, due_at ASC);

CREATE TABLE IF NOT EXISTS workflow_events (
    id TEXT PRIMARY KEY,
    workflow_item_id TEXT NOT NULL,
    action TEXT NOT NULL,
    previous_state TEXT NOT NULL,
    new_state TEXT NOT NULL,
    actor TEXT NOT NULL,
    comment TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(workflow_item_id) REFERENCES workflow_items(id)
);

CREATE INDEX IF NOT EXISTS idx_workflow_events_item
ON workflow_events(workflow_item_id, created_at ASC, id ASC);
"""


class SqliteWorkflowRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    async def add(self, item: WorkflowItem) -> None:
        await asyncio.to_thread(self._add, item)

    async def update(self, item: WorkflowItem, event: WorkflowEvent) -> None:
        await asyncio.to_thread(self._update, item, event)

    async def get(self, item_id: WorkflowItemId) -> WorkflowItem | None:
        return await asyncio.to_thread(self._get, item_id)

    async def list_by_project(self, project_id: str) -> list[WorkflowItem]:
        return await asyncio.to_thread(self._list_by_project, project_id)

    async def list_events(self, item_id: WorkflowItemId) -> list[WorkflowEvent]:
        return await asyncio.to_thread(self._list_events, item_id)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(_SCHEMA)

    def _add(self, item: WorkflowItem) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO workflow_items (
                    id, workspace_id, project_id, entity_type, entity_id, title,
                    priority, state, assignee, created_by, due_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._item_record(item),
            )

    def _update(self, item: WorkflowItem, event: WorkflowEvent) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE workflow_items
                SET state = ?, assignee = ?, priority = ?, due_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    item.state.value,
                    item.assignee,
                    item.priority.value,
                    item.due_at.isoformat(),
                    item.updated_at.isoformat(),
                    str(item.id),
                ),
            )
            connection.execute(
                """
                INSERT INTO workflow_events (
                    id, workflow_item_id, action, previous_state, new_state,
                    actor, comment, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(event.id),
                    str(event.workflow_item_id),
                    event.action.value,
                    event.previous_state.value,
                    event.new_state.value,
                    event.actor,
                    event.comment,
                    event.created_at.isoformat(),
                ),
            )

    def _get(self, item_id: WorkflowItemId) -> WorkflowItem | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM workflow_items WHERE id = ?",
                (str(item_id),),
            ).fetchone()
        return self._item_from_row(row) if row is not None else None

    def _list_by_project(self, project_id: str) -> list[WorkflowItem]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM workflow_items
                WHERE project_id = ?
                ORDER BY CASE state
                    WHEN 'OPEN' THEN 0
                    WHEN 'TRIAGED' THEN 1
                    WHEN 'IN_PROGRESS' THEN 2
                    WHEN 'IN_REVIEW' THEN 3
                    WHEN 'APPROVED' THEN 4
                    WHEN 'CLOSED' THEN 5
                    ELSE 6 END,
                    CASE priority
                    WHEN 'P0' THEN 0
                    WHEN 'P1' THEN 1
                    WHEN 'P2' THEN 2
                    ELSE 3 END,
                    due_at ASC,
                    id ASC
                """,
                (project_id,),
            ).fetchall()
        return [self._item_from_row(row) for row in rows]

    def _list_events(self, item_id: WorkflowItemId) -> list[WorkflowEvent]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM workflow_events
                WHERE workflow_item_id = ?
                ORDER BY created_at ASC, id ASC
                """,
                (str(item_id),),
            ).fetchall()
        return [self._event_from_row(row) for row in rows]

    @staticmethod
    def _item_record(item: WorkflowItem) -> tuple[object, ...]:
        return (
            str(item.id),
            item.workspace_id,
            item.project_id,
            item.entity_type.value,
            item.entity_id,
            item.title,
            item.priority.value,
            item.state.value,
            item.assignee,
            item.created_by,
            item.due_at.isoformat(),
            item.created_at.isoformat(),
            item.updated_at.isoformat(),
        )

    @staticmethod
    def _item_from_row(row: sqlite3.Row) -> WorkflowItem:
        return WorkflowItem(
            id=WorkflowItemId.from_string(str(row["id"])),
            workspace_id=str(row["workspace_id"]),
            project_id=str(row["project_id"]),
            entity_type=WorkflowEntityType(str(row["entity_type"])),
            entity_id=str(row["entity_id"]),
            title=str(row["title"]),
            priority=WorkflowPriority(str(row["priority"])),
            state=WorkflowState(str(row["state"])),
            assignee=str(row["assignee"]),
            created_by=str(row["created_by"]),
            due_at=datetime.fromisoformat(str(row["due_at"])),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )

    @staticmethod
    def _event_from_row(row: sqlite3.Row) -> WorkflowEvent:
        return WorkflowEvent(
            id=WorkflowEventId.from_string(str(row["id"])),
            workflow_item_id=WorkflowItemId.from_string(str(row["workflow_item_id"])),
            action=WorkflowAction(str(row["action"])),
            previous_state=WorkflowState(str(row["previous_state"])),
            new_state=WorkflowState(str(row["new_state"])),
            actor=str(row["actor"]),
            comment=str(row["comment"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )
