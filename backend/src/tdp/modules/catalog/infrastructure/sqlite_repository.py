import asyncio
import json
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import cast

from tdp.modules.catalog.domain.model import (
    ApiOperation,
    ApiParameter,
    ApiPayload,
    ApiResponse,
    ApiSchema,
    ApiSchemaProperty,
    SynchronizationId,
    SynchronizationRun,
    SynchronizationStatus,
)
from tdp.modules.catalog.domain.repository import CatalogRepository

_SCHEMA = """
CREATE TABLE IF NOT EXISTS catalog_sync_runs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_checksum TEXT NOT NULL,
    status TEXT NOT NULL,
    operation_count INTEGER NOT NULL,
    schema_count INTEGER NOT NULL,
    error_code TEXT NOT NULL,
    error_message TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY(project_id) REFERENCES projects(id),
    FOREIGN KEY(source_id) REFERENCES sources(id)
);
CREATE INDEX IF NOT EXISTS idx_catalog_runs_source_started
ON catalog_sync_runs(source_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_catalog_runs_project_status
ON catalog_sync_runs(project_id, status, completed_at DESC);

CREATE TABLE IF NOT EXISTS api_operations (
    synchronization_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    method TEXT NOT NULL,
    path TEXT NOT NULL,
    operation_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    description TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    deprecated INTEGER NOT NULL,
    security_json TEXT NOT NULL,
    parameters_json TEXT NOT NULL,
    request_body_json TEXT,
    responses_json TEXT NOT NULL,
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(synchronization_id, method, path),
    FOREIGN KEY(synchronization_id) REFERENCES catalog_sync_runs(id)
);
CREATE INDEX IF NOT EXISTS idx_api_operations_project_source
ON api_operations(project_id, source_id, method, path);

CREATE TABLE IF NOT EXISTS api_schemas (
    synchronization_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    name TEXT NOT NULL,
    schema_type TEXT NOT NULL,
    description TEXT NOT NULL,
    required_fields_json TEXT NOT NULL,
    properties_json TEXT NOT NULL,
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(synchronization_id, name),
    FOREIGN KEY(synchronization_id) REFERENCES catalog_sync_runs(id)
);
CREATE INDEX IF NOT EXISTS idx_api_schemas_project_source
ON api_schemas(project_id, source_id, name);
"""


class SqliteCatalogRepository(CatalogRepository):
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    async def add_run(self, run: SynchronizationRun) -> None:
        await asyncio.to_thread(self._add_run, run)

    async def complete_run(
        self,
        run: SynchronizationRun,
        operations: list[ApiOperation],
        schemas: list[ApiSchema],
    ) -> None:
        await asyncio.to_thread(self._complete_run, run, operations, schemas)

    async def update_run(self, run: SynchronizationRun) -> None:
        await asyncio.to_thread(self._update_run, run)

    async def get_run(self, run_id: SynchronizationId) -> SynchronizationRun | None:
        return await asyncio.to_thread(self._get_run, run_id)

    async def list_runs_by_source(self, source_id: str) -> list[SynchronizationRun]:
        return await asyncio.to_thread(self._list_runs_by_source, source_id)

    async def list_latest_runs(
        self,
        project_id: str,
        source_id: str | None = None,
    ) -> list[SynchronizationRun]:
        return await asyncio.to_thread(self._list_latest_runs, project_id, source_id)

    async def list_current_operations(
        self,
        project_id: str,
        source_id: str | None = None,
    ) -> list[ApiOperation]:
        return await asyncio.to_thread(
            self._list_current_operations,
            project_id,
            source_id,
        )

    async def list_current_schemas(
        self,
        project_id: str,
        source_id: str | None = None,
    ) -> list[ApiSchema]:
        return await asyncio.to_thread(
            self._list_current_schemas,
            project_id,
            source_id,
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(_SCHEMA)

    def _add_run(self, run: SynchronizationRun) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO catalog_sync_runs (
                    id, project_id, source_id, source_checksum, status,
                    operation_count, schema_count, error_code, error_message,
                    started_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._run_record(run),
            )

    def _complete_run(
        self,
        run: SynchronizationRun,
        operations: list[ApiOperation],
        schemas: list[ApiSchema],
    ) -> None:
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO api_operations (
                    synchronization_id, project_id, source_id, method, path,
                    operation_id, summary, description, tags_json, deprecated,
                    security_json, parameters_json, request_body_json,
                    responses_json, source_pointer
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [self._operation_record(operation) for operation in operations],
            )
            connection.executemany(
                """
                INSERT INTO api_schemas (
                    synchronization_id, project_id, source_id, name, schema_type,
                    description, required_fields_json, properties_json, source_pointer
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [self._schema_record(schema) for schema in schemas],
            )
            self._update_run_in_connection(connection, run)

    def _update_run(self, run: SynchronizationRun) -> None:
        with self._connect() as connection:
            self._update_run_in_connection(connection, run)

    @staticmethod
    def _update_run_in_connection(
        connection: sqlite3.Connection,
        run: SynchronizationRun,
    ) -> None:
        connection.execute(
            """
            UPDATE catalog_sync_runs
            SET status = ?, operation_count = ?, schema_count = ?,
                error_code = ?, error_message = ?, completed_at = ?
            WHERE id = ?
            """,
            (
                run.status.value,
                run.operation_count,
                run.schema_count,
                run.error_code,
                run.error_message,
                run.completed_at.isoformat() if run.completed_at is not None else None,
                str(run.id),
            ),
        )

    def _get_run(self, run_id: SynchronizationId) -> SynchronizationRun | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM catalog_sync_runs WHERE id = ?",
                (str(run_id),),
            ).fetchone()
        return self._run_from_row(row) if row is not None else None

    def _list_runs_by_source(self, source_id: str) -> list[SynchronizationRun]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM catalog_sync_runs
                WHERE source_id = ?
                ORDER BY started_at DESC, id DESC
                """,
                (source_id,),
            ).fetchall()
        return [self._run_from_row(row) for row in rows]

    def _list_latest_runs(
        self,
        project_id: str,
        source_id: str | None,
    ) -> list[SynchronizationRun]:
        where_source, parameters = self._source_filter(project_id, source_id, alias="run")
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT run.*
                FROM catalog_sync_runs AS run
                WHERE run.status = 'COMPLETED'
                  AND {where_source}
                  AND run.id = (
                      SELECT candidate.id
                      FROM catalog_sync_runs AS candidate
                      WHERE candidate.source_id = run.source_id
                        AND candidate.status = 'COMPLETED'
                      ORDER BY candidate.completed_at DESC, candidate.started_at DESC,
                               candidate.id DESC
                      LIMIT 1
                  )
                ORDER BY run.completed_at DESC, run.source_id ASC
                """,
                parameters,
            ).fetchall()
        return [self._run_from_row(row) for row in rows]

    def _list_current_operations(
        self,
        project_id: str,
        source_id: str | None,
    ) -> list[ApiOperation]:
        where_source, parameters = self._source_filter(project_id, source_id, alias="operation")
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT operation.*
                FROM api_operations AS operation
                WHERE {where_source}
                  AND operation.synchronization_id = (
                      SELECT run.id
                      FROM catalog_sync_runs AS run
                      WHERE run.source_id = operation.source_id
                        AND run.status = 'COMPLETED'
                      ORDER BY run.completed_at DESC, run.started_at DESC, run.id DESC
                      LIMIT 1
                  )
                ORDER BY operation.path ASC, operation.method ASC
                """,
                parameters,
            ).fetchall()
        return [self._operation_from_row(row) for row in rows]

    def _list_current_schemas(
        self,
        project_id: str,
        source_id: str | None,
    ) -> list[ApiSchema]:
        where_source, parameters = self._source_filter(project_id, source_id, alias="schema")
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT schema.*
                FROM api_schemas AS schema
                WHERE {where_source}
                  AND schema.synchronization_id = (
                      SELECT run.id
                      FROM catalog_sync_runs AS run
                      WHERE run.source_id = schema.source_id
                        AND run.status = 'COMPLETED'
                      ORDER BY run.completed_at DESC, run.started_at DESC, run.id DESC
                      LIMIT 1
                  )
                ORDER BY schema.name ASC
                """,
                parameters,
            ).fetchall()
        return [self._schema_from_row(row) for row in rows]

    @staticmethod
    def _source_filter(
        project_id: str,
        source_id: str | None,
        *,
        alias: str,
    ) -> tuple[str, tuple[str, ...]]:
        if source_id is None:
            return f"{alias}.project_id = ?", (project_id,)
        return (
            f"{alias}.project_id = ? AND {alias}.source_id = ?",
            (project_id, source_id),
        )

    @staticmethod
    def _run_record(run: SynchronizationRun) -> tuple[object, ...]:
        return (
            str(run.id),
            run.project_id,
            run.source_id,
            run.source_checksum,
            run.status.value,
            run.operation_count,
            run.schema_count,
            run.error_code,
            run.error_message,
            run.started_at.isoformat(),
            run.completed_at.isoformat() if run.completed_at is not None else None,
        )

    @staticmethod
    def _operation_record(operation: ApiOperation) -> tuple[object, ...]:
        return (
            str(operation.synchronization_id),
            operation.project_id,
            operation.source_id,
            operation.method,
            operation.path,
            operation.operation_id,
            operation.summary,
            operation.description,
            json.dumps(list(operation.tags), separators=(",", ":")),
            int(operation.deprecated),
            json.dumps(list(operation.security_schemes), separators=(",", ":")),
            json.dumps(
                [asdict(parameter) for parameter in operation.parameters],
                separators=(",", ":"),
            ),
            (
                json.dumps(asdict(operation.request_body), separators=(",", ":"))
                if operation.request_body is not None
                else None
            ),
            json.dumps(
                [asdict(response) for response in operation.responses],
                separators=(",", ":"),
            ),
            operation.source_pointer,
        )

    @staticmethod
    def _schema_record(schema: ApiSchema) -> tuple[object, ...]:
        return (
            str(schema.synchronization_id),
            schema.project_id,
            schema.source_id,
            schema.name,
            schema.schema_type,
            schema.description,
            json.dumps(list(schema.required_fields), separators=(",", ":")),
            json.dumps(
                [asdict(property_item) for property_item in schema.properties],
                separators=(",", ":"),
            ),
            schema.source_pointer,
        )

    @staticmethod
    def _run_from_row(row: sqlite3.Row) -> SynchronizationRun:
        completed_at = row["completed_at"]
        return SynchronizationRun(
            id=SynchronizationId.from_string(str(row["id"])),
            project_id=str(row["project_id"]),
            source_id=str(row["source_id"]),
            source_checksum=str(row["source_checksum"]),
            status=SynchronizationStatus(str(row["status"])),
            operation_count=int(row["operation_count"]),
            schema_count=int(row["schema_count"]),
            error_code=str(row["error_code"]),
            error_message=str(row["error_message"]),
            started_at=datetime.fromisoformat(str(row["started_at"])),
            completed_at=(
                datetime.fromisoformat(str(completed_at)) if completed_at is not None else None
            ),
        )

    @classmethod
    def _operation_from_row(cls, row: sqlite3.Row) -> ApiOperation:
        parameters = cls._json_sequence(row["parameters_json"], "parameters_json")
        request_body_value = row["request_body_json"]
        responses = cls._json_sequence(row["responses_json"], "responses_json")
        return ApiOperation(
            synchronization_id=SynchronizationId.from_string(str(row["synchronization_id"])),
            project_id=str(row["project_id"]),
            source_id=str(row["source_id"]),
            method=str(row["method"]),
            path=str(row["path"]),
            operation_id=str(row["operation_id"]),
            summary=str(row["summary"]),
            description=str(row["description"]),
            tags=cls._json_string_tuple(row["tags_json"]),
            deprecated=bool(row["deprecated"]),
            security_schemes=cls._json_string_tuple(row["security_json"]),
            parameters=tuple(cls._parameter_from_mapping(item) for item in parameters),
            request_body=(
                cls._payload_from_mapping(
                    cls._json_mapping(request_body_value, "request_body_json")
                )
                if request_body_value is not None
                else None
            ),
            responses=tuple(cls._response_from_mapping(item) for item in responses),
            source_pointer=str(row["source_pointer"]),
        )

    @classmethod
    def _schema_from_row(cls, row: sqlite3.Row) -> ApiSchema:
        properties = cls._json_sequence(row["properties_json"], "properties_json")
        return ApiSchema(
            synchronization_id=SynchronizationId.from_string(str(row["synchronization_id"])),
            project_id=str(row["project_id"]),
            source_id=str(row["source_id"]),
            name=str(row["name"]),
            schema_type=str(row["schema_type"]),
            description=str(row["description"]),
            required_fields=cls._json_string_tuple(row["required_fields_json"]),
            properties=tuple(cls._schema_property_from_mapping(item) for item in properties),
            source_pointer=str(row["source_pointer"]),
        )

    @staticmethod
    def _json_value(value: object) -> object:
        if not isinstance(value, str):
            raise ValueError("Stored catalog JSON must be text.")
        return cast(object, json.loads(value))

    @classmethod
    def _json_sequence(cls, value: object, label: str) -> Sequence[Mapping[str, object]]:
        decoded = cls._json_value(value)
        if not isinstance(decoded, Sequence) or isinstance(decoded, (str, bytes, bytearray)):
            raise ValueError(f"{label} must contain a JSON array.")
        mappings: list[Mapping[str, object]] = []
        for item in decoded:
            if not isinstance(item, Mapping):
                raise ValueError(f"{label} entries must be JSON objects.")
            mappings.append(cast(Mapping[str, object], item))
        return mappings

    @classmethod
    def _json_mapping(cls, value: object, label: str) -> Mapping[str, object]:
        decoded = cls._json_value(value)
        if not isinstance(decoded, Mapping):
            raise ValueError(f"{label} must contain a JSON object.")
        return cast(Mapping[str, object], decoded)

    @classmethod
    def _json_string_tuple(cls, value: object) -> tuple[str, ...]:
        decoded = cls._json_value(value)
        if not isinstance(decoded, Sequence) or isinstance(decoded, (str, bytes, bytearray)):
            raise ValueError("Stored catalog string collection must be a JSON array.")
        return tuple(str(item) for item in decoded)

    @staticmethod
    def _string_tuple(mapping: Mapping[str, object], key: str) -> tuple[str, ...]:
        value = mapping.get(key)
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
            return ()
        return tuple(str(item) for item in value)

    @classmethod
    def _parameter_from_mapping(
        cls,
        mapping: Mapping[str, object],
    ) -> ApiParameter:
        return ApiParameter(
            name=str(mapping.get("name", "")),
            location=str(mapping.get("location", "")),
            required=mapping.get("required") is True,
            schema_type=str(mapping.get("schema_type", "")),
            schema_format=str(mapping.get("schema_format", "")),
            schema_reference=str(mapping.get("schema_reference", "")),
        )

    @classmethod
    def _payload_from_mapping(cls, mapping: Mapping[str, object]) -> ApiPayload:
        return ApiPayload(
            required=mapping.get("required") is True,
            media_types=cls._string_tuple(mapping, "media_types"),
            schema_types=cls._string_tuple(mapping, "schema_types"),
            schema_references=cls._string_tuple(mapping, "schema_references"),
        )

    @classmethod
    def _response_from_mapping(cls, mapping: Mapping[str, object]) -> ApiResponse:
        return ApiResponse(
            status_code=str(mapping.get("status_code", "")),
            description=str(mapping.get("description", "")),
            media_types=cls._string_tuple(mapping, "media_types"),
            schema_types=cls._string_tuple(mapping, "schema_types"),
            schema_references=cls._string_tuple(mapping, "schema_references"),
        )

    @staticmethod
    def _schema_property_from_mapping(
        mapping: Mapping[str, object],
    ) -> ApiSchemaProperty:
        return ApiSchemaProperty(
            name=str(mapping.get("name", "")),
            schema_type=str(mapping.get("schema_type", "")),
            schema_format=str(mapping.get("schema_format", "")),
            required=mapping.get("required") is True,
            reference=str(mapping.get("reference", "")),
            description=str(mapping.get("description", "")),
        )
