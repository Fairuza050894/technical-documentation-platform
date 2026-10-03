from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from tdp.modules.changes.domain.model import Change, ChangeSeverity, Comparison


class ImpactLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


_DOCUMENT_ORDER = (
    "HLD",
    "LLD",
    "AS_BUILT",
    "USER_GUIDE",
    "UAT_EVIDENCE",
)


@dataclass(frozen=True, slots=True)
class ChangeImpact:
    entity_type: str
    entity_key: str
    level: ImpactLevel
    required_document_types: tuple[str, ...]
    requirement_review_required: bool
    test_execution_required: bool
    rationale: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ImpactAssessment:
    project_id: str
    baseline_run_id: str
    target_run_id: str
    level: ImpactLevel
    required_document_types: tuple[str, ...]
    requirement_review_required: bool
    test_execution_required: bool
    impacts: tuple[ChangeImpact, ...]


class DeterministicChangeImpactPolicy:
    """Maps catalog changes to explicit review obligations without AI inference."""

    def assess(self, comparison: Comparison) -> ImpactAssessment:
        impacts = tuple(self._assess_change(change) for change in comparison.changes)
        required_documents = self._ordered_documents(
            document_type
            for impact in impacts
            for document_type in impact.required_document_types
        )
        return ImpactAssessment(
            project_id=comparison.project_id,
            baseline_run_id=comparison.baseline_run_id,
            target_run_id=comparison.target_run_id,
            level=max(
                (impact.level for impact in impacts),
                key=self._level_rank,
                default=ImpactLevel.LOW,
            ),
            required_document_types=required_documents,
            requirement_review_required=any(
                impact.requirement_review_required for impact in impacts
            ),
            test_execution_required=any(impact.test_execution_required for impact in impacts),
            impacts=impacts,
        )

    def _assess_change(self, change: Change) -> ChangeImpact:
        documents: set[str] = {"LLD", "AS_BUILT"}
        rationale = [change.summary]
        requirement_review_required = False
        test_execution_required = change.entity_type in {"OPERATION", "SCHEMA"}

        if change.severity is ChangeSeverity.BREAKING:
            level = ImpactLevel.CRITICAL
            documents.update({"HLD", "USER_GUIDE", "UAT_EVIDENCE"})
            requirement_review_required = True
            rationale.append("Breaking contract change requires requirement and release-impact review.")
        elif change.severity is ChangeSeverity.POTENTIALLY_BREAKING:
            level = ImpactLevel.HIGH
            documents.add("UAT_EVIDENCE")
            requirement_review_required = True
            rationale.append("Potential contract break requires requirement review before release.")
        else:
            level = ImpactLevel.MEDIUM
            rationale.append("Non-breaking technical change still requires as-built documentation review.")

        if "security_before" in change.details or "security_after" in change.details:
            documents.add("HLD")
            requirement_review_required = True
            level = max(level, ImpactLevel.HIGH, key=self._level_rank)
            rationale.append("Security contract changed; architecture and requirement review are required.")

        return ChangeImpact(
            entity_type=change.entity_type,
            entity_key=change.entity_key,
            level=level,
            required_document_types=self._ordered_documents(documents),
            requirement_review_required=requirement_review_required,
            test_execution_required=test_execution_required,
            rationale=tuple(rationale),
        )

    @staticmethod
    def _ordered_documents(values: Iterable[str]) -> tuple[str, ...]:
        present = set(values)
        return tuple(item for item in _DOCUMENT_ORDER if item in present)

    @staticmethod
    def _level_rank(level: ImpactLevel) -> int:
        return {
            ImpactLevel.LOW: 0,
            ImpactLevel.MEDIUM: 1,
            ImpactLevel.HIGH: 2,
            ImpactLevel.CRITICAL: 3,
        }[level]
