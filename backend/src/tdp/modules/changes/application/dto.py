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
    level: str
    required_document_types: list[str]
    requirement_review_required: bool
    test_execution_required: bool
    impacts: list[dict[str, Any]]

    @classmethod
    def from_domain(cls, assessment: ImpactAssessment) -> "ImpactAssessmentDto":
        return cls(
            project_id=assessment.project_id,
            baseline_run_id=assessment.baseline_run_id,
            target_run_id=assessment.target_run_id,
            level=assessment.level.value,
            required_document_types=list(assessment.required_document_types),
            requirement_review_required=assessment.requirement_review_required,
            test_execution_required=assessment.test_execution_required,
            impacts=[asdict(item) for item in assessment.impacts],
        )
