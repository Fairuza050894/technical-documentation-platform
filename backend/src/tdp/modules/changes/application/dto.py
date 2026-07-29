from dataclasses import asdict, dataclass
from typing import Any

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
