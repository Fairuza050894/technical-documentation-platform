import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path

from tdp.modules.features.domain.errors import FeatureKeyAlreadyExistsError
from tdp.modules.features.domain.model import (
    DocumentationRequirement,
    DocumentationType,
    Feature,
    FeatureDescription,
    FeatureDocumentationMapItem,
    FeatureId,
    FeatureKey,
    FeatureKind,
    FeatureName,
    FeatureOwner,
    FeatureStatus,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS features (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    feature_key TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    kind TEXT NOT NULL,
    owner TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, feature_key),
    FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE INDEX IF NOT EXISTS idx_features_project_status
ON features(project_id, status, created_at ASC, id ASC);

CREATE TABLE IF NOT EXISTS feature_documentation_map (
    feature_id TEXT NOT NULL,
    document_type TEXT NOT NULL,
    requirement TEXT NOT NULL,
    document_id TEXT,
    policy_key TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY(feature_id, document_type),
    FOREIGN KEY(feature_id) REFERENCES features(id)
);

CREATE INDEX IF NOT EXISTS idx_feature_documentation_map_feature
ON feature_documentation_map(feature_id, requirement, document_type);
"""


class SqliteFeatureRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    async def add(
        self,
        feature: Feature,
        documentation_map: list[FeatureDocumentationMapItem],
    ) -> None:
        try:
            await asyncio.to_thread(self._add, feature, documentation_map)
        except sqlite3.IntegrityError as exc:
            raise FeatureKeyAlreadyExistsError(
                f"Feature key {feature.key} is already in use inside project {feature.project_id}."
            ) from exc

    async def update(self, feature: Feature) -> None:
        await asyncio.to_thread(self._update, feature)

    async def get(self, feature_id: FeatureId) -> Feature | None:
        return await asyncio.to_thread(self._get, feature_id)

    async def get_by_project_key(
        self,
        project_id: str,
        key: FeatureKey,
    ) -> Feature | None:
        return await asyncio.to_thread(self._get_by_project_key, project_id, key)

    async def list_by_project(self, project_id: str) -> list[Feature]:
        return await asyncio.to_thread(self._list_by_project, project_id)

    async def list_documentation_map(
        self,
        feature_id: FeatureId,
    ) -> list[FeatureDocumentationMapItem]:
        return await asyncio.to_thread(self._list_documentation_map, feature_id)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(_SCHEMA)

    def _add(
        self,
        feature: Feature,
        documentation_map: list[FeatureDocumentationMapItem],
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO features (
                    id, project_id, feature_key, name, description, kind,
                    owner, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._feature_record(feature),
            )
            connection.executemany(
                """
                INSERT INTO feature_documentation_map (
                    feature_id, document_type, requirement, document_id,
                    policy_key, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [self._map_record(item) for item in documentation_map],
            )

    def _update(self, feature: Feature) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE features
                SET project_id = ?, feature_key = ?, name = ?, description = ?,
                    kind = ?, owner = ?, status = ?, created_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    feature.project_id,
                    str(feature.key),
                    str(feature.name),
                    str(feature.description),
                    feature.kind.value,
                    str(feature.owner),
                    feature.status.value,
                    feature.created_at.isoformat(),
                    feature.updated_at.isoformat(),
                    str(feature.id),
                ),
            )

    def _get(self, feature_id: FeatureId) -> Feature | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM features WHERE id = ?",
                (str(feature_id),),
            ).fetchone()
        return self._feature_from_row(row) if row is not None else None

    def _get_by_project_key(
        self,
        project_id: str,
        key: FeatureKey,
    ) -> Feature | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM features WHERE project_id = ? AND feature_key = ?",
                (project_id, str(key)),
            ).fetchone()
        return self._feature_from_row(row) if row is not None else None

    def _list_by_project(self, project_id: str) -> list[Feature]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM features
                WHERE project_id = ?
                ORDER BY CASE status WHEN 'ACTIVE' THEN 0 ELSE 1 END,
                         created_at ASC,
                         id ASC
                """,
                (project_id,),
            ).fetchall()
        return [self._feature_from_row(row) for row in rows]

    def _list_documentation_map(
        self,
        feature_id: FeatureId,
    ) -> list[FeatureDocumentationMapItem]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM feature_documentation_map
                WHERE feature_id = ?
                ORDER BY document_type ASC
                """,
                (str(feature_id),),
            ).fetchall()
        return [self._map_from_row(row) for row in rows]

    @staticmethod
    def _feature_record(feature: Feature) -> tuple[str, ...]:
        return (
            str(feature.id),
            feature.project_id,
            str(feature.key),
            str(feature.name),
            str(feature.description),
            feature.kind.value,
            str(feature.owner),
            feature.status.value,
            feature.created_at.isoformat(),
            feature.updated_at.isoformat(),
        )

    @staticmethod
    def _map_record(item: FeatureDocumentationMapItem) -> tuple[str | None, ...]:
        return (
            str(item.feature_id),
            item.document_type.value,
            item.requirement.value,
            item.document_id,
            item.policy_key,
            item.created_at.isoformat(),
            item.updated_at.isoformat(),
        )

    @staticmethod
    def _feature_from_row(row: sqlite3.Row) -> Feature:
        return Feature(
            id=FeatureId.from_string(str(row["id"])),
            project_id=str(row["project_id"]),
            key=FeatureKey(str(row["feature_key"])),
            name=FeatureName(str(row["name"])),
            description=FeatureDescription(str(row["description"])),
            kind=FeatureKind(str(row["kind"])),
            owner=FeatureOwner(str(row["owner"])),
            status=FeatureStatus(str(row["status"])),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )

    @staticmethod
    def _map_from_row(row: sqlite3.Row) -> FeatureDocumentationMapItem:
        return FeatureDocumentationMapItem(
            feature_id=FeatureId.from_string(str(row["feature_id"])),
            document_type=DocumentationType(str(row["document_type"])),
            requirement=DocumentationRequirement(str(row["requirement"])),
            document_id=str(row["document_id"]) if row["document_id"] is not None else None,
            policy_key=str(row["policy_key"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )
