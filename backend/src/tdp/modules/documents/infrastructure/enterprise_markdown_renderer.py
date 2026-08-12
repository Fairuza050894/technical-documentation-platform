from tdp.modules.documents.application.enterprise_generation_ports import (
    EnterpriseGenerationContext,
    GenerationClaimFact,
    GenerationOperationFact,
    GenerationSchemaFact,
)
from tdp.modules.documents.domain.model import DocumentType


class DeterministicEnterpriseMarkdownRenderer:
    def render(self, context: EnterpriseGenerationContext) -> str:
        if context.profile.document_type is DocumentType.HLD:
            return self._render_hld(context)
        if context.profile.document_type is DocumentType.AS_BUILT:
            return self._render_as_built(context)
        if context.profile.document_type is not DocumentType.LLD:
            raise ValueError(
                f"Unsupported enterprise renderer profile: {context.profile.document_type.value}"
            )

        operations = sorted(context.operations, key=lambda item: (item.path, item.method))
        schemas = sorted(context.schemas, key=lambda item: item.name)
        rendered_classifications = set(context.profile.rendered_claim_classifications)
        observed = sorted(
            (
                item
                for item in context.claims
                if item.classification == "OBSERVED" and "OBSERVED" in rendered_classifications
            ),
            key=lambda item: item.id,
        )
        inferred = sorted(
            (
                item
                for item in context.claims
                if item.classification == "INFERRED" and "INFERRED" in rendered_classifications
            ),
            key=lambda item: item.id,
        )
        unverified_total = sum(item.classification == "UNVERIFIED" for item in context.claims)

        lines = [
            f"# Low Level Design: {self._text(context.project_name)}",
            "",
            (
                "> Deterministically generated from governed normalized API evidence. "
                "No AI-generated factual content is used."
            ),
            "",
            "## Document control",
            "",
            "| Field | Value |",
            "| --- | --- |",
            (
                f"| Project | {self._cell(context.project_key)} — "
                f"{self._cell(context.project_name)} |"
            ),
            f"| Workspace ID | `{self._code(context.workspace_id)}` |",
            f"| Document type | `{context.profile.document_type.value}` |",
            f"| Generation profile | `{context.profile.profile_key}` |",
            f"| Readiness policy | `{self._code(context.readiness.policy_version)}` |",
            f"| Readiness state | `{self._code(context.readiness.state)}` |",
            f"| Source | {self._cell(context.source_name)} |",
            f"| API title | {self._cell(context.api_title)} |",
            f"| OpenAPI version | {self._cell(context.openapi_version)} |",
            f"| API version | {self._cell(context.api_version)} |",
            (
                "| Target synchronization | "
                f"`{self._code(context.target_run_id or 'Not applicable')}` |"
            ),
            f"| Source checksum | `{self._code(context.source_checksum)}` |",
            f"| Primary evidence | `{self._code(context.primary_evidence_id)}` |",
            (
                "| Snapshot completed at | "
                f"{self._cell(context.snapshot_completed_at or 'Not applicable')} |"
            ),
            "",
            "## Scope and generation basis",
            "",
            self._paragraph(
                context.project_description,
                "No project description was provided.",
            ),
            "",
            (
                "This initial LLD profile describes the implementation contract visible in the "
                "selected normalized API Catalog snapshot."
            ),
            "",
            f"- Operations represented: **{len(operations)}**",
            f"- Component schemas represented: **{len(schemas)}**",
            f"- Project Catalog snapshots available: **{context.available_snapshot_count}**",
            "",
            "## API operations",
            "",
        ]

        if operations:
            for operation in operations:
                lines.extend(self._operation_section(operation))
        else:
            lines.extend(["No operations were present in the selected snapshot.", ""])

        lines.extend(["## Component schemas", ""])
        if schemas:
            for schema in schemas:
                lines.extend(self._schema_section(schema))
        else:
            lines.extend(["No component schemas were present in the selected snapshot.", ""])

        lines.extend(["## Governed contextual claims", ""])
        if observed:
            lines.extend(["### Observed", ""])
            for claim in observed:
                lines.extend(self._claim_lines(claim, inferred=False))
        if inferred:
            lines.extend(["### Inferred", ""])
            for claim in inferred:
                lines.extend(self._claim_lines(claim, inferred=True))
        if not observed and not inferred:
            lines.extend(
                [
                    "No observed or deterministically inferred LLD-relevant claims were available.",
                    "",
                ]
            )

        lines.extend(["## Readiness findings", ""])
        if context.readiness.findings:
            for finding in context.readiness.findings:
                lines.extend(
                    [
                        f"### {self._text(finding.rule_code)}",
                        "",
                        f"- Severity: **{self._text(finding.severity)}**",
                        f"- Finding: {self._text(finding.message)}",
                        f"- Missing input: `{self._code(finding.missing_input)}`",
                        f"- Remediation: {self._text(finding.remediation)}",
                        "",
                    ]
                )
        else:
            lines.extend(
                [
                    "No blocker or warning remains under the current readiness policy.",
                    "",
                ]
            )

        lines.extend(
            [
                "## Traceability",
                "",
                "| Evidence ID | Kind | Checksum | Source reference |",
                "| --- | --- | --- | --- |",
            ]
        )
        for evidence in sorted(context.evidence, key=lambda item: (item.kind, item.id)):
            lines.append(
                f"| `{self._code(evidence.id)}` | {self._cell(evidence.kind)} | "
                f"`{self._code(evidence.checksum)}` | "
                f"`{self._code(evidence.source_reference)}` |"
            )

        lines.extend(
            [
                "",
                "## Known gaps and generation policy",
                "",
                (
                    "- Factual API and schema content comes only from the selected normalized "
                    "Catalog snapshot."
                ),
                (
                    "- OBSERVED claims are rendered as governed context only when they are "
                    "explicitly relevant to LLD."
                ),
                (
                    "- INFERRED claims are always labelled Inferred and preserve their "
                    "deterministic derivation reference."
                ),
                (
                    f"- UNVERIFIED LLD-relevant claims excluded from factual sections: "
                    f"**{unverified_total}**."
                ),
                (
                    "- The current generation foundation selects the latest governed Catalog "
                    "snapshot evidence deterministically."
                ),
                (
                    "- Regenerating from identical canonical inputs produces identical Markdown "
                    "content and checksum."
                ),
                "- AI does not determine factual truth, readiness, or rendered technical facts.",
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    def _render_hld(self, context: EnterpriseGenerationContext) -> str:
        operations = sorted(context.operations, key=lambda item: (item.path, item.method))
        schemas = sorted(context.schemas, key=lambda item: item.name)
        rendered_classifications = set(context.profile.rendered_claim_classifications)
        observed = sorted(
            (
                item
                for item in context.claims
                if item.classification == "OBSERVED" and "OBSERVED" in rendered_classifications
            ),
            key=lambda item: item.id,
        )
        inferred = sorted(
            (
                item
                for item in context.claims
                if item.classification == "INFERRED" and "INFERRED" in rendered_classifications
            ),
            key=lambda item: item.id,
        )
        unverified_total = sum(item.classification == "UNVERIFIED" for item in context.claims)
        has_catalog_snapshot = context.target_run_id is not None

        lines = [
            f"# High Level Design: {self._text(context.project_name)}",
            "",
            (
                "> Deterministically generated from governed technical evidence and explicitly "
                "classified architectural context. No AI-generated factual content is used."
            ),
            "",
            "## Document control",
            "",
            "| Field | Value |",
            "| --- | --- |",
            (
                f"| Project | {self._cell(context.project_key)} — "
                f"{self._cell(context.project_name)} |"
            ),
            f"| Workspace ID | `{self._code(context.workspace_id)}` |",
            f"| Document type | `{context.profile.document_type.value}` |",
            f"| Generation profile | `{context.profile.profile_key}` |",
            f"| Readiness policy | `{self._code(context.readiness.policy_version)}` |",
            f"| Readiness state | `{self._code(context.readiness.state)}` |",
            f"| Source | {self._cell(context.source_name)} |",
            f"| API title | {self._cell(context.api_title)} |",
            f"| OpenAPI version | {self._cell(context.openapi_version)} |",
            f"| API version | {self._cell(context.api_version)} |",
            f"| Source checksum | `{self._code(context.source_checksum)}` |",
            f"| Primary evidence kind | `{self._code(context.primary_evidence_kind)}` |",
            f"| Primary evidence | `{self._code(context.primary_evidence_id)}` |",
            (
                "| Target synchronization | "
                f"`{self._code(context.target_run_id or 'Not applicable')}` |"
                if has_catalog_snapshot
                else "| Target synchronization | Not applicable — source evidence |"
            ),
            (
                f"| Snapshot completed at | {self._cell(context.snapshot_completed_at or '')} |"
                if has_catalog_snapshot
                else "| Snapshot completed at | Not applicable — source evidence |"
            ),
            "",
            "## Purpose and architecture boundary",
            "",
            self._paragraph(
                context.project_description,
                "No project description was provided.",
            ),
            "",
            (
                "This HLD establishes only the high-level system boundary supported by the "
                "selected governed evidence. Architectural rationale that is not directly "
                "observable must remain an explicitly classified governed claim."
            ),
            "",
            "## Technical evidence summary",
            "",
            f"- Source: **{self._text(context.source_name)}**",
            (
                f"- API contract: **{self._text(context.api_title)} "
                f"{self._text(context.api_version)}**"
            ),
            f"- Primary evidence kind: **{self._text(context.primary_evidence_kind)}**",
        ]

        if has_catalog_snapshot:
            lines.extend(
                [
                    f"- Normalized API operations represented: **{len(operations)}**",
                    f"- Normalized component schemas represented: **{len(schemas)}**",
                    (
                        "- Project Catalog snapshots available: "
                        f"**{context.available_snapshot_count}**"
                    ),
                    "",
                    "### Normalized API boundary",
                    "",
                    "| Method | Path | Capability | Evidence |",
                    "| --- | --- | --- | --- |",
                ]
            )
            if operations:
                for operation in operations:
                    capability = operation.summary or operation.operation_id or "Not provided"
                    lines.append(
                        f"| `{self._code(operation.method)}` | `{self._code(operation.path)}` | "
                        f"{self._cell(capability)} | "
                        f"`{self._code(operation.source_pointer)}` |"
                    )
            else:
                lines.append("| — | — | No normalized operations were present. | — |")
            lines.extend(
                [
                    "",
                    (
                        "Normalized schemas are recorded as supporting implementation "
                        f"boundary evidence (**{len(schemas)}** schemas) rather than "
                        "expanded as LLD detail."
                    ),
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "",
                    (
                        "The canonical HLD readiness policy accepts any governed technical "
                        "evidence. This draft therefore remains valid with SOURCE_ARTIFACT "
                        "evidence even when no Catalog snapshot exists."
                    ),
                    (
                        "Normalized endpoint and schema inventory is unavailable in this draft; "
                        "generation does not invent a synchronization or implementation detail."
                    ),
                    "",
                ]
            )

        lines.extend(["## Governed architectural context", ""])
        if observed:
            lines.extend(["### Observed", ""])
            for claim in observed:
                lines.extend(self._claim_lines(claim, inferred=False))
        if inferred:
            lines.extend(["### Inferred", ""])
            for claim in inferred:
                lines.extend(self._claim_lines(claim, inferred=True))
        if not observed and not inferred:
            lines.extend(
                [
                    (
                        "No observed or deterministically inferred HLD-relevant architectural "
                        "claim was available. The readiness warning below remains visible."
                    ),
                    "",
                ]
            )

        lines.extend(["## Readiness findings", ""])
        if context.readiness.findings:
            for finding in context.readiness.findings:
                lines.extend(
                    [
                        f"### {self._text(finding.rule_code)}",
                        "",
                        f"- Severity: **{self._text(finding.severity)}**",
                        f"- Finding: {self._text(finding.message)}",
                        f"- Missing input: `{self._code(finding.missing_input)}`",
                        f"- Remediation: {self._text(finding.remediation)}",
                        "",
                    ]
                )
        else:
            lines.extend(
                [
                    "No blocker or warning remains under the current readiness policy.",
                    "",
                ]
            )

        lines.extend(
            [
                "## Evidence traceability",
                "",
                "| Evidence ID | Kind | Checksum | Source reference |",
                "| --- | --- | --- | --- |",
            ]
        )
        for evidence in sorted(context.evidence, key=lambda item: (item.kind, item.id)):
            lines.append(
                f"| `{self._code(evidence.id)}` | {self._cell(evidence.kind)} | "
                f"`{self._code(evidence.checksum)}` | "
                f"`{self._code(evidence.source_reference)}` |"
            )

        lines.extend(
            [
                "",
                "## Known gaps and generation policy",
                "",
                (
                    "- Component topology, runtime placement, infrastructure ownership, "
                    "non-functional requirements, data flows, and architecture decisions are "
                    "not asserted unless governed evidence or claims support them."
                ),
                (
                    "- OBSERVED claims are rendered as directly governed context; INFERRED "
                    "claims remain visibly labelled and preserve their deterministic derivation."
                ),
                (
                    f"- UNVERIFIED HLD-relevant claims excluded from factual sections: "
                    f"**{unverified_total}**."
                ),
                (
                    "- Evidence selection is deterministic across the evidence kinds accepted "
                    "by the profile and never adds a stronger generation prerequisite than the "
                    "canonical readiness policy."
                ),
                (
                    "- Regenerating from identical canonical inputs produces identical Markdown "
                    "content and checksum."
                ),
                "- AI does not determine factual truth, readiness, or architectural facts.",
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    def _render_as_built(self, context: EnterpriseGenerationContext) -> str:
        operations = sorted(context.operations, key=lambda item: (item.path, item.method))
        schemas = sorted(context.schemas, key=lambda item: item.name)
        rendered_classifications = set(context.profile.rendered_claim_classifications)
        observed = sorted(
            (
                item
                for item in context.claims
                if item.classification == "OBSERVED" and "OBSERVED" in rendered_classifications
            ),
            key=lambda item: item.id,
        )
        excluded = sorted(
            (item for item in context.claims if item.classification != "OBSERVED"),
            key=lambda item: (item.classification, item.id),
        )
        inferred_total = sum(item.classification == "INFERRED" for item in excluded)
        unverified_total = sum(item.classification == "UNVERIFIED" for item in excluded)

        lines = [
            f"# As-Built Documentation: {self._text(context.project_name)}",
            "",
            (
                "> Deterministically generated from governed normalized API evidence and "
                "OBSERVED As-Built claims. No AI-generated factual content is used."
            ),
            "",
            "## Document control",
            "",
            "| Field | Value |",
            "| --- | --- |",
            (
                f"| Project | {self._cell(context.project_key)} — "
                f"{self._cell(context.project_name)} |"
            ),
            f"| Workspace ID | `{self._code(context.workspace_id)}` |",
            f"| Document type | `{context.profile.document_type.value}` |",
            f"| Generation profile | `{context.profile.profile_key}` |",
            f"| Readiness policy | `{self._code(context.readiness.policy_version)}` |",
            f"| Readiness state | `{self._code(context.readiness.state)}` |",
            f"| Source | {self._cell(context.source_name)} |",
            f"| API title | {self._cell(context.api_title)} |",
            f"| OpenAPI version | {self._cell(context.openapi_version)} |",
            f"| API version | {self._cell(context.api_version)} |",
            (
                "| Target synchronization | "
                f"`{self._code(context.target_run_id or 'Not applicable')}` |"
            ),
            f"| Source checksum | `{self._code(context.source_checksum)}` |",
            f"| Primary evidence | `{self._code(context.primary_evidence_id)}` |",
            (
                "| Snapshot completed at | "
                f"{self._cell(context.snapshot_completed_at or 'Not applicable')} |"
            ),
            "",
            "## Scope and evidence boundary",
            "",
            self._paragraph(
                context.project_description,
                "No project description was provided.",
            ),
            "",
            (
                "This As-Built draft records only the implementation surface visible in the "
                "selected normalized API Catalog snapshot and explicit OBSERVED claims relevant "
                "to As-Built Documentation."
            ),
            "",
            f"- Operations represented: **{len(operations)}**",
            f"- Component schemas represented: **{len(schemas)}**",
            f"- Observed As-Built claims represented: **{len(observed)}**",
            f"- Project Catalog snapshots available: **{context.available_snapshot_count}**",
            "",
            "## Observed implementation assertions",
            "",
        ]

        if observed:
            for claim in observed:
                lines.extend(self._claim_lines(claim, inferred=False))
        else:
            lines.extend(
                [
                    (
                        "No OBSERVED As-Built claim is present in this rendering context. "
                        "Canonical readiness normally blocks generation before this point."
                    ),
                    "",
                ]
            )

        lines.extend(["## Normalized API implementation inventory", "", "### API operations", ""])
        if operations:
            for operation in operations:
                lines.extend(self._operation_section(operation))
        else:
            lines.extend(["No operations were present in the selected snapshot.", ""])

        lines.extend(["### Component schemas", ""])
        if schemas:
            for schema in schemas:
                lines.extend(self._schema_section(schema))
        else:
            lines.extend(["No component schemas were present in the selected snapshot.", ""])

        lines.extend(["## Readiness findings", ""])
        if context.readiness.findings:
            for finding in context.readiness.findings:
                lines.extend(
                    [
                        f"### {self._text(finding.rule_code)}",
                        "",
                        f"- Severity: **{self._text(finding.severity)}**",
                        f"- Finding: {self._text(finding.message)}",
                        f"- Missing input: `{self._code(finding.missing_input)}`",
                        f"- Remediation: {self._text(finding.remediation)}",
                        "",
                    ]
                )
        else:
            lines.extend(
                [
                    "No blocker or warning remains under the current readiness policy.",
                    "",
                ]
            )

        lines.extend(
            [
                "## Evidence traceability",
                "",
                "| Evidence ID | Kind | Checksum | Source reference |",
                "| --- | --- | --- | --- |",
            ]
        )
        for evidence in sorted(context.evidence, key=lambda item: (item.kind, item.id)):
            lines.append(
                f"| `{self._code(evidence.id)}` | {self._cell(evidence.kind)} | "
                f"`{self._code(evidence.checksum)}` | "
                f"`{self._code(evidence.source_reference)}` |"
            )

        lines.extend(["", "## Excluded non-observed claim references", ""])
        if excluded:
            for claim in excluded:
                lines.append(
                    f"- `{self._code(claim.id)}` — **{self._text(claim.classification)}** — "
                    "excluded from factual As-Built content."
                )
            lines.append("")
        else:
            lines.extend(["No non-observed As-Built claims were present.", ""])

        lines.extend(
            [
                "## Known gaps and generation policy",
                "",
                (
                    "- API and schema inventory is limited to the selected normalized "
                    "Catalog snapshot."
                ),
                (
                    "- Only OBSERVED claims explicitly relevant to AS_BUILT are rendered as "
                    "confirmed implementation assertions."
                ),
                (
                    f"- INFERRED As-Built claims excluded from factual sections: "
                    f"**{inferred_total}**."
                ),
                (
                    f"- UNVERIFIED As-Built claims excluded from factual sections: "
                    f"**{unverified_total}**."
                ),
                (
                    "- Deployment topology, runtime configuration, database topology, operational "
                    "procedures, and user journeys are not asserted unless governed evidence "
                    "explicitly supports them."
                ),
                (
                    "- Regenerating from identical canonical inputs produces identical Markdown "
                    "content and checksum."
                ),
                (
                    "- AI does not determine factual truth, readiness, or rendered "
                    "implementation facts."
                ),
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    def _operation_section(self, operation: GenerationOperationFact) -> list[str]:
        lines = [
            f"### `{self._code(operation.method)} {self._code(operation.path)}`",
            "",
            self._paragraph(operation.summary, "No operation summary was provided."),
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| Operation ID | {self._cell(operation.operation_id or 'Not provided')} |",
            f"| Tags | {self._cell(self._plain_list(operation.tags))} |",
            f"| Deprecated | {'Yes' if operation.deprecated else 'No'} |",
            f"| Security | {self._cell(self._plain_list(operation.security_schemes))} |",
            f"| Source pointer | `{self._code(operation.source_pointer)}` |",
            "",
        ]
        if operation.description.strip():
            lines.extend(
                [
                    "**Description**",
                    "",
                    self._text(operation.description),
                    "",
                ]
            )

        lines.extend(["**Parameters**", ""])
        if operation.parameters:
            lines.extend(f"- {self._text(item)}" for item in operation.parameters)
        else:
            lines.append("- None")
        lines.extend(
            [
                "",
                "**Request body**",
                "",
                f"- {self._text(operation.request_body)}",
                "",
                "**Responses**",
                "",
            ]
        )
        if operation.responses:
            lines.extend(f"- {self._text(item)}" for item in operation.responses)
        else:
            lines.append("- None")
        lines.append("")
        return lines

    def _schema_section(self, schema: GenerationSchemaFact) -> list[str]:
        lines = [
            f"### {self._text(schema.name)}",
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| Type | {self._cell(schema.schema_type or 'unspecified')} |",
            f"| Required fields | {self._cell(self._plain_list(schema.required_fields))} |",
            f"| Source pointer | `{self._code(schema.source_pointer)}` |",
            "",
        ]
        if schema.description.strip():
            lines.extend(
                [
                    self._text(schema.description),
                    "",
                ]
            )
        lines.extend(["**Properties**", ""])
        if schema.properties:
            lines.extend(f"- {self._text(item)}" for item in schema.properties)
        else:
            lines.append("- None")
        lines.append("")
        return lines

    def _claim_lines(
        self,
        claim: GenerationClaimFact,
        *,
        inferred: bool,
    ) -> list[str]:
        lines = [
            f"- **{'Inferred' if inferred else 'Observed'}** — {self._text(claim.statement)}",
            f"  - Claim: `{self._code(claim.id)}`",
            (
                "  - Evidence: "
                + (
                    ", ".join(f"`{self._code(item)}`" for item in claim.evidence_ids)
                    if claim.evidence_ids
                    else "None"
                )
            ),
        ]
        if inferred:
            lines.append(f"  - Derivation: `{self._code(claim.derivation_reference)}`")
        lines.append("")
        return lines

    @staticmethod
    def _plain_list(values: tuple[str, ...]) -> str:
        return ", ".join(values) if values else "None"

    @classmethod
    def _paragraph(cls, value: str, fallback: str) -> str:
        normalized = " ".join(value.split())
        return cls._text(normalized or fallback)

    @staticmethod
    def _text(value: str) -> str:
        return value.replace("\r", " ").replace("\n", " ").strip()

    @classmethod
    def _cell(cls, value: str) -> str:
        return cls._text(value).replace("|", "\\|")

    @staticmethod
    def _code(value: str) -> str:
        return value.replace("`", "'").replace("\r", " ").replace("\n", " ").strip()
