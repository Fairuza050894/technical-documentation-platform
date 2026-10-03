from dataclasses import dataclass
from enum import StrEnum

from tdp.modules.changes.domain.model import Change, ChangeKind, ChangeSeverity, Comparison


class ImpactPriority(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class ImpactAction(StrEnum):
    UPDATE_REQUIRED = "UPDATE_REQUIRED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"


@dataclass(frozen=True, slots=True)
class ImpactItem:
    document_type: str
    action: ImpactAction
    priority: ImpactPriority
    reason: str
    source_changes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ImpactAssessment:
    project_id: str
    baseline_run_id: str
    target_run_id: str
    policy_key: str
    approval_required: bool
    requirement_revalidation_required: bool
    highest_priority: ImpactPriority
    items: tuple[ImpactItem, ...]


class DeterministicImpactPolicy:
    policy_key = "api-change-impact-v1"

    def assess(self, comparison: Comparison) -> ImpactAssessment:
        if not comparison.changes:
            return ImpactAssessment(
                project_id=comparison.project_id,
                baseline_run_id=comparison.baseline_run_id,
                target_run_id=comparison.target_run_id,
                policy_key=self.policy_key,
                approval_required=False,
                requirement_revalidation_required=False,
                highest_priority=ImpactPriority.P3,
                items=(),
            )

        breaking = [item for item in comparison.changes if item.severity is ChangeSeverity.BREAKING]
        potential = [
            item
            for item in comparison.changes
            if item.severity is ChangeSeverity.POTENTIALLY_BREAKING
        ]
        requirement_revalidation_required = any(
            item.kind in {ChangeKind.MODIFIED, ChangeKind.REMOVED} for item in comparison.changes
        )

        document_changes: dict[str, list[Change]] = {
            "TECHNICAL_SOURCE_OVERVIEW": list(comparison.changes),
            "LLD": list(comparison.changes),
        }
        if breaking or potential:
            document_changes["HLD"] = [*breaking, *potential]
            document_changes["UAT_EVIDENCE"] = [*breaking, *potential]
        if breaking:
            document_changes["USER_GUIDE"] = breaking
            document_changes["AS_BUILT"] = breaking

        items = tuple(
            self._impact_item(document_type, changes)
            for document_type, changes in sorted(document_changes.items())
        )
        highest_priority = min(
            (item.priority for item in items),
            key=lambda value: _PRIORITY_ORDER[value],
        )
        return ImpactAssessment(
            project_id=comparison.project_id,
            baseline_run_id=comparison.baseline_run_id,
            target_run_id=comparison.target_run_id,
            policy_key=self.policy_key,
            approval_required=bool(breaking),
            requirement_revalidation_required=requirement_revalidation_required,
            highest_priority=highest_priority,
            items=items,
        )

    @staticmethod
    def _impact_item(document_type: str, changes: list[Change]) -> ImpactItem:
        breaking_total = sum(item.severity is ChangeSeverity.BREAKING for item in changes)
        potential_total = sum(
            item.severity is ChangeSeverity.POTENTIALLY_BREAKING for item in changes
        )
        labels = tuple(item.entity_key for item in changes)
        if breaking_total > 0:
            return ImpactItem(
                document_type=document_type,
                action=ImpactAction.APPROVAL_REQUIRED,
                priority=ImpactPriority.P1,
                reason=(
                    f"{breaking_total} breaking change(s) affect this document profile; "
                    "update and governed approval are required."
                ),
                source_changes=labels,
            )
        if potential_total > 0:
            return ImpactItem(
                document_type=document_type,
                action=ImpactAction.UPDATE_REQUIRED,
                priority=ImpactPriority.P2,
                reason=(
                    f"{potential_total} potentially breaking change(s) require content "
                    "revalidation and update."
                ),
                source_changes=labels,
            )
        return ImpactItem(
            document_type=document_type,
            action=ImpactAction.REVIEW_REQUIRED,
            priority=ImpactPriority.P3,
            reason="Non-breaking source changes require freshness review.",
            source_changes=labels,
        )


_PRIORITY_ORDER = {
    ImpactPriority.P0: 0,
    ImpactPriority.P1: 1,
    ImpactPriority.P2: 2,
    ImpactPriority.P3: 3,
}
