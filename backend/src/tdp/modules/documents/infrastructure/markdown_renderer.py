from collections.abc import Iterable
from datetime import datetime

from tdp.modules.catalog.domain.model import ApiOperation, ApiSchema
from tdp.modules.changes.domain.model import ChangeSeverity
from tdp.modules.documents.application.ports import TechnicalSourceOverviewContext


class DeterministicTechnicalSourceOverviewRenderer:
    def render(self, context: TechnicalSourceOverviewContext) -> str:
        operations = sorted(context.operations, key=lambda item: (item.path, item.method))
        schemas = sorted(context.schemas, key=lambda item: item.name)
        security_schemes = sorted(
            {scheme for operation in operations for scheme in operation.security_schemes if scheme}
        )
        tags = sorted({tag for operation in operations for tag in operation.tags if tag})

        lines = [
            f"# Technical Source Overview: {self._text(context.source.api_title)}",
            "",
            "> Deterministically generated from a normalized OpenAPI synchronization snapshot.",
            "",
            "## Document control",
            "",
            "| Field | Value |",
            "| --- | --- |",
            (
                f"| Project | {self._cell(str(context.project.key))} — "
                f"{self._cell(str(context.project.name))} |"
            ),
            f"| Workspace ID | `{context.project.workspace_id}` |",
            f"| Ownership | {self._cell(context.project.ownership_type.value.title())} |",
            f"| Source | {self._cell(str(context.source.name))} |",
            f"| Source type | {self._cell(context.source.source_type.value)} |",
            f"| Original file | {self._cell(str(context.source.original_file_name))} |",
            f"| OpenAPI version | {self._cell(context.source.openapi_version)} |",
            f"| API version | {self._cell(context.source.api_version)} |",
            f"| Target synchronization | `{context.target_run.id}` |",
            f"| Source checksum | `{context.target_run.source_checksum}` |",
            (
                "| Snapshot completed at | "
                f"{self._cell(self._timestamp(context.target_run.completed_at))} |"
            ),
            "",
            "## Project overview",
            "",
            self._paragraph(
                str(context.project.description),
                "No project description was provided.",
            ),
            "",
            "## API summary",
            "",
            f"- Operations: **{len(operations)}**",
            f"- Component schemas: **{len(schemas)}**",
            f"- Security schemes: {self._inline_list(security_schemes)}",
            f"- Tags: {self._inline_list(tags)}",
            "",
            "## Endpoint catalog",
            "",
        ]

        if operations:
            for operation in operations:
                lines.extend(self._operation_section(operation))
        else:
            lines.extend(
                [
                    "No operations were found in the selected synchronization snapshot.",
                    "",
                ]
            )

        lines.extend(["## Component schemas", ""])
        if schemas:
            for schema in schemas:
                lines.extend(self._schema_section(schema))
        else:
            lines.extend(
                [
                    "No component schemas were found in the selected synchronization snapshot.",
                    "",
                ]
            )

        lines.extend(self._change_summary(context))
        lines.extend(
            [
                "## Traceability and generation policy",
                "",
                (
                    "- All technical facts in this document come from the selected "
                    "normalized snapshot."
                ),
                "- JSON Pointer evidence is preserved for each operation and component schema.",
                "- The renderer does not use AI and does not infer missing technical facts.",
                (
                    "- Regenerating from the same normalized inputs produces identical "
                    "Markdown content."
                ),
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    def _operation_section(self, operation: ApiOperation) -> list[str]:
        lines = [
            f"### `{operation.method} {self._text(operation.path)}`",
            "",
            self._paragraph(operation.summary, "No summary was provided."),
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| Operation ID | {self._cell(operation.operation_id or 'Not provided')} |",
            f"| Tags | {self._cell(self._plain_list(operation.tags))} |",
            f"| Deprecated | {'Yes' if operation.deprecated else 'No'} |",
            f"| Security | {self._cell(self._plain_list(operation.security_schemes))} |",
            f"| Source evidence | `{self._code(operation.source_pointer)}` |",
            "",
            "#### Parameters",
            "",
        ]
        if operation.parameters:
            lines.extend(
                [
                    "| Name | Location | Required | Type | Format | Reference |",
                    "| --- | --- | --- | --- | --- | --- |",
                ]
            )
            for parameter in operation.parameters:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            self._cell(parameter.name),
                            self._cell(parameter.location),
                            "Yes" if parameter.required else "No",
                            self._cell(parameter.schema_type or "Not specified"),
                            self._cell(parameter.schema_format or "—"),
                            self._cell(parameter.schema_reference or "—"),
                        ]
                    )
                    + " |"
                )
        else:
            lines.append("No parameters were declared.")

        lines.extend(["", "#### Request body", ""])
        if operation.request_body is None:
            lines.append("No request body was declared.")
        else:
            lines.extend(
                [
                    f"- Required: **{'Yes' if operation.request_body.required else 'No'}**",
                    f"- Media types: {self._inline_list(operation.request_body.media_types)}",
                    f"- Schema types: {self._inline_list(operation.request_body.schema_types)}",
                    (
                        "- Schema references: "
                        f"{self._inline_list(operation.request_body.schema_references, code=True)}"
                    ),
                ]
            )

        lines.extend(["", "#### Responses", ""])
        if operation.responses:
            lines.extend(
                [
                    "| Status | Description | Media types | Schema types | Schema references |",
                    "| --- | --- | --- | --- | --- |",
                ]
            )
            for response in operation.responses:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            self._cell(response.status_code),
                            self._cell(response.description or "No description"),
                            self._cell(self._plain_list(response.media_types)),
                            self._cell(self._plain_list(response.schema_types)),
                            self._cell(self._plain_list(response.schema_references)),
                        ]
                    )
                    + " |"
                )
        else:
            lines.append("No responses were declared.")
        lines.append("")
        return lines

    def _schema_section(self, schema: ApiSchema) -> list[str]:
        lines = [
            f"### `{self._code(schema.name)}`",
            "",
            self._paragraph(schema.description, "No schema description was provided."),
            "",
            f"- Type: `{self._code(schema.schema_type or 'Not specified')}`",
            f"- Required fields: {self._inline_list(schema.required_fields, code=True)}",
            f"- Source evidence: `{self._code(schema.source_pointer)}`",
            "",
            "| Property | Type | Format | Required | Reference | Description |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        if schema.properties:
            for property_item in schema.properties:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            self._cell(property_item.name),
                            self._cell(property_item.schema_type or "Not specified"),
                            self._cell(property_item.schema_format or "—"),
                            "Yes" if property_item.required else "No",
                            self._cell(property_item.reference or "—"),
                            self._cell(property_item.description or "—"),
                        ]
                    )
                    + " |"
                )
        else:
            lines.append("| _No properties_ | — | — | — | — | — |")
        lines.append("")
        return lines

    def _change_summary(self, context: TechnicalSourceOverviewContext) -> list[str]:
        comparison = context.comparison
        lines = ["## Breaking-change summary", ""]
        if comparison is None:
            return [
                *lines,
                "No baseline synchronization was selected. Change impact was not calculated.",
                "",
            ]

        breaking = [
            change for change in comparison.changes if change.severity is ChangeSeverity.BREAKING
        ]
        lines.extend(
            [
                f"- Baseline synchronization: `{comparison.baseline_run_id}`",
                f"- Target synchronization: `{comparison.target_run_id}`",
                f"- Total detected changes: **{len(comparison.changes)}**",
                f"- Breaking changes: **{len(breaking)}**",
                "",
            ]
        )
        if not breaking:
            lines.extend(["No deterministic breaking changes were detected.", ""])
            return lines

        lines.extend(["### Breaking changes requiring review", ""])
        for change in breaking:
            evidence = change.after_pointer or change.before_pointer or "Not available"
            lines.extend(
                [
                    (
                        f"- **{change.entity_type} `{self._code(change.entity_key)}` — "
                        f"{change.kind.value}**"
                    ),
                    f"  - {self._text(change.summary)}",
                    f"  - Evidence: `{self._code(evidence)}`",
                ]
            )
        lines.append("")
        return lines

    @staticmethod
    def _timestamp(value: datetime | None) -> str:
        return value.isoformat() if value is not None else "Not available"

    @staticmethod
    def _text(value: str) -> str:
        return " ".join(value.split())

    def _paragraph(self, value: str, fallback: str) -> str:
        normalized = self._text(value)
        return normalized or fallback

    def _cell(self, value: str) -> str:
        return self._text(value).replace("|", "\\|") or "—"

    @staticmethod
    def _code(value: str) -> str:
        return value.replace("`", "\\`")

    def _plain_list(self, values: Iterable[str]) -> str:
        normalized = [self._text(value) for value in values if self._text(value)]
        return ", ".join(normalized) if normalized else "None"

    def _inline_list(self, values: Iterable[str], *, code: bool = False) -> str:
        normalized = sorted({self._text(value) for value in values if self._text(value)})
        if not normalized:
            return "None"
        if code:
            return ", ".join(f"`{self._code(value)}`" for value in normalized)
        return ", ".join(normalized)
