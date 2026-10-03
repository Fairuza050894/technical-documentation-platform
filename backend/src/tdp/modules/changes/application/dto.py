from dataclasses import asdict, dataclass
from typing import Any

from tdp.modules.changes.domain.impact import ImpactAssessment
from tdp.modules.changes.domain.model import Comparison


@dataclass(frozen=True, slots=True)
class ComparisonDto:
    project_id: str
    baseline_run_id: str
    target_run_id: str
    total: int
    breaking_total: int
    changes: list[dict[str, Any]]

    @classmethod
    def from_domain(cls, comparison: Comparison) -> "ComparisonDto":
        return cls(
            project_id=comparison.project_id,
            baseline_run_id=comparison.baseline_run_id,
            target_run_id=comparison.target_run_id,
            total=len(comparison.changes),
            breaking_total=comparison.breaking_total,
            changes=[asdict(item) for item in comparison.changes],
        )


@dataclass(frozen=True, slots=True)
class ImpactAssessmentDto:
    project_id: str
    baseline_run_id: str
    target_run_id: str
    policy_key: str
    approval_required: bool
    requirement_revalidation_required: bool
    highest_priority: str
    items: list[dict[str, Any]]

    @classmethod
    def from_domain(cls, assessment: ImpactAssessment) -> "ImpactAssessmentDto":
        return cls(
            project_id=assessment.project_id,
            baseline_run_id=assessment.baseline_run_id,
            target_run_id=assessment.target_run_id,
            policy_key=assessment.policy_key,
            approval_required=assessment.approval_required,
            requirement_revalidation_required=assessment.requirement_revalidation_required,
            highest_priority=assessment.highest_priority.value,
            items=[
                {
                    "document_type": item.document_type,
                    "action": item.action.value,
                    "priority": item.priority.value,
                    "reason": item.reason,
                    "source_changes": list(item.source_changes),
                }
                for item in assessment.items
            ],
        )
