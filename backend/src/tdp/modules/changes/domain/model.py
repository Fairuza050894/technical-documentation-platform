from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from tdp.modules.catalog.domain.model import ApiOperation, ApiSchema


class ChangeKind(StrEnum):
    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    REMOVED = "REMOVED"


class ChangeSeverity(StrEnum):
    NON_BREAKING = "NON_BREAKING"
    POTENTIALLY_BREAKING = "POTENTIALLY_BREAKING"
    BREAKING = "BREAKING"


@dataclass(frozen=True, slots=True)
class Change:
    entity_type: str
    entity_key: str
    kind: ChangeKind
    severity: ChangeSeverity
    summary: str
    before_pointer: str
    after_pointer: str
    details: dict[str, Any]


@dataclass(frozen=True, slots=True)
class Comparison:
    project_id: str
    baseline_run_id: str
    target_run_id: str
    changes: tuple[Change, ...]

    @property
    def breaking_total(self) -> int:
        return sum(item.severity is ChangeSeverity.BREAKING for item in self.changes)


class DeterministicCatalogComparator:
    def compare(
        self,
        *,
        project_id: str,
        baseline_run_id: str,
        target_run_id: str,
        baseline_operations: list[ApiOperation],
        target_operations: list[ApiOperation],
        baseline_schemas: list[ApiSchema],
        target_schemas: list[ApiSchema],
    ) -> Comparison:
        changes = [
            *self._compare_operations(baseline_operations, target_operations),
            *self._compare_schemas(baseline_schemas, target_schemas),
        ]
        ordered_changes = sorted(
            changes,
            key=lambda item: (item.entity_type, item.entity_key, item.kind),
        )
        return Comparison(
            project_id=project_id,
            baseline_run_id=baseline_run_id,
            target_run_id=target_run_id,
            changes=tuple(ordered_changes),
        )

    def _compare_operations(
        self,
        baseline: list[ApiOperation],
        target: list[ApiOperation],
    ) -> list[Change]:
        before = {(item.method, item.path): item for item in baseline}
        after = {(item.method, item.path): item for item in target}
        changes: list[Change] = []

        for key in sorted(before.keys() | after.keys()):
            old = before.get(key)
            new = after.get(key)
            label = f"{key[0]} {key[1]}"
            if old is None and new is not None:
                changes.append(
                    Change(
                        entity_type="OPERATION",
                        entity_key=label,
                        kind=ChangeKind.ADDED,
                        severity=ChangeSeverity.NON_BREAKING,
                        summary=f"Operation {label} was added.",
                        before_pointer="",
                        after_pointer=new.source_pointer,
                        details={},
                    )
                )
            elif old is not None and new is None:
                changes.append(
                    Change(
                        entity_type="OPERATION",
                        entity_key=label,
                        kind=ChangeKind.REMOVED,
                        severity=ChangeSeverity.BREAKING,
                        summary=f"Operation {label} was removed.",
                        before_pointer=old.source_pointer,
                        after_pointer="",
                        details={},
                    )
                )
            elif old is not None and new is not None:
                details = self._operation_details(old, new)
                if details:
                    breaking_keys = {
                        "removed_responses",
                        "new_required_parameters",
                        "request_became_required",
                    }
                    severity = (
                        ChangeSeverity.BREAKING
                        if breaking_keys.intersection(details)
                        else ChangeSeverity.POTENTIALLY_BREAKING
                    )
                    changes.append(
                        Change(
                            entity_type="OPERATION",
                            entity_key=label,
                            kind=ChangeKind.MODIFIED,
                            severity=severity,
                            summary=f"Operation {label} changed.",
                            before_pointer=old.source_pointer,
                            after_pointer=new.source_pointer,
                            details=details,
                        )
                    )
        return changes

    @staticmethod
    def _operation_details(old: ApiOperation, new: ApiOperation) -> dict[str, Any]:
        details: dict[str, Any] = {}
        old_responses = {item.status_code for item in old.responses}
        new_responses = {item.status_code for item in new.responses}
        removed = sorted(old_responses - new_responses)
        added = sorted(new_responses - old_responses)
        if removed:
            details["removed_responses"] = removed
        if added:
            details["added_responses"] = added

        old_required = {(item.location, item.name) for item in old.parameters if item.required}
        new_required = {(item.location, item.name) for item in new.parameters if item.required}
        required_added = sorted(
            f"{location}:{name}" for location, name in new_required - old_required
        )
        if required_added:
            details["new_required_parameters"] = required_added

        if (
            old.request_body is not None
            and new.request_body is not None
            and not old.request_body.required
            and new.request_body.required
        ):
            details["request_became_required"] = True
        elif old.request_body is None and new.request_body is not None:
            details["request_body_added"] = True
        elif old.request_body is not None and new.request_body is None:
            details["request_body_removed"] = True

        if old.security_schemes != new.security_schemes:
            details["security_before"] = list(old.security_schemes)
            details["security_after"] = list(new.security_schemes)
        return details

    def _compare_schemas(
        self,
        baseline: list[ApiSchema],
        target: list[ApiSchema],
    ) -> list[Change]:
        before = {item.name: item for item in baseline}
        after = {item.name: item for item in target}
        changes: list[Change] = []

        for name in sorted(before.keys() | after.keys()):
            old = before.get(name)
            new = after.get(name)
            if old is None and new is not None:
                changes.append(
                    Change(
                        entity_type="SCHEMA",
                        entity_key=name,
                        kind=ChangeKind.ADDED,
                        severity=ChangeSeverity.NON_BREAKING,
                        summary=f"Schema {name} was added.",
                        before_pointer="",
                        after_pointer=new.source_pointer,
                        details={},
                    )
                )
            elif old is not None and new is None:
                changes.append(
                    Change(
                        entity_type="SCHEMA",
                        entity_key=name,
                        kind=ChangeKind.REMOVED,
                        severity=ChangeSeverity.BREAKING,
                        summary=f"Schema {name} was removed.",
                        before_pointer=old.source_pointer,
                        after_pointer="",
                        details={},
                    )
                )
            elif old is not None and new is not None:
                old_properties = {item.name: item for item in old.properties}
                new_properties = {item.name: item for item in new.properties}
                removed = sorted(old_properties.keys() - new_properties.keys())
                added = sorted(new_properties.keys() - old_properties.keys())
                newly_required = sorted(set(new.required_fields) - set(old.required_fields))
                details: dict[str, Any] = {}
                if removed:
                    details["removed_properties"] = removed
                if added:
                    details["added_properties"] = added
                if newly_required:
                    details["new_required_fields"] = newly_required
                if details:
                    severity = (
                        ChangeSeverity.BREAKING
                        if removed or newly_required
                        else ChangeSeverity.NON_BREAKING
                    )
                    changes.append(
                        Change(
                            entity_type="SCHEMA",
                            entity_key=name,
                            kind=ChangeKind.MODIFIED,
                            severity=severity,
                            summary=f"Schema {name} changed.",
                            before_pointer=old.source_pointer,
                            after_pointer=new.source_pointer,
                            details=details,
                        )
                    )
        return changes
