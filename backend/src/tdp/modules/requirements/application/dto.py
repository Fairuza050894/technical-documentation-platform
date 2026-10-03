from dataclasses import dataclass

from tdp.modules.requirements.domain.model import RequirementRevision, TraceLink


@dataclass(frozen=True, slots=True)
class TraceLinkDto:
    id: str
    target_type: str
    relation: str
    target_reference: str
    verified: bool
    created_by: str
    created_at: str

    @classmethod
    def from_domain(cls, link: TraceLink) -> "TraceLinkDto":
        return cls(
            id=str(link.id),
            target_type=link.target_type.value,
            relation=link.relation.value,
            target_reference=link.target_reference,
            verified=link.verified,
            created_by=link.created_by,
            created_at=link.created_at.isoformat(),
        )


@dataclass(frozen=True, slots=True)
class RequirementDto:
    requirement_id: str
    revision_id: str
    project_id: str
    key: str
    revision: int
    requirement_type: str
    status: str
    title: str
    statement: str
    owner: str
    feature_id: str | None
    acceptance_criteria: tuple[str, ...]
    changed_by: str
    change_reason: str
    created_at: str
    trace_links: tuple[TraceLinkDto, ...]

    @classmethod
    def from_domain(
        cls,
        revision: RequirementRevision,
        trace_links: list[TraceLink],
    ) -> "RequirementDto":
        return cls(
            requirement_id=str(revision.requirement_id),
            revision_id=str(revision.revision_id),
            project_id=revision.project_id,
            key=str(revision.key),
            revision=revision.revision,
            requirement_type=revision.requirement_type.value,
            status=revision.status.value,
            title=revision.title,
            statement=revision.statement,
            owner=revision.owner,
            feature_id=revision.feature_id,
            acceptance_criteria=revision.acceptance_criteria,
            changed_by=revision.changed_by,
            change_reason=revision.change_reason,
            created_at=revision.created_at.isoformat(),
            trace_links=tuple(TraceLinkDto.from_domain(link) for link in trace_links),
        )


@dataclass(frozen=True, slots=True)
class TraceabilityCoverageDto:
    total_requirements: int
    linked_to_feature: int
    linked_to_evidence: int
    linked_to_document: int
    fully_traced: int

    @property
    def coverage_percent(self) -> int:
        if self.total_requirements == 0:
            return 0
        return round((self.fully_traced / self.total_requirements) * 100)
