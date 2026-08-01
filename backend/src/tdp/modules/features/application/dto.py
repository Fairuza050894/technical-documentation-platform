from dataclasses import dataclass

from tdp.modules.features.domain.model import Feature, FeatureDocumentationMapItem


@dataclass(frozen=True, slots=True)
class FeatureCoverageDto:
    required_total: int
    available_required: int
    missing_required: int
    optional_total: int


@dataclass(frozen=True, slots=True)
class FeatureDto:
    id: str
    project_id: str
    key: str
    name: str
    description: str
    kind: str
    owner: str
    status: str
    documentation_coverage: FeatureCoverageDto
    created_at: str
    updated_at: str

    @classmethod
    def from_domain(
        cls,
        feature: Feature,
        documentation_map: list[FeatureDocumentationMapItem],
    ) -> "FeatureDto":
        required = [item for item in documentation_map if item.requirement.value == "REQUIRED"]
        available_required = sum(item.document_id is not None for item in required)
        return cls(
            id=str(feature.id),
            project_id=feature.project_id,
            key=str(feature.key),
            name=str(feature.name),
            description=str(feature.description),
            kind=feature.kind.value,
            owner=str(feature.owner),
            status=feature.status.value,
            documentation_coverage=FeatureCoverageDto(
                required_total=len(required),
                available_required=available_required,
                missing_required=len(required) - available_required,
                optional_total=len(documentation_map) - len(required),
            ),
            created_at=feature.created_at.isoformat(),
            updated_at=feature.updated_at.isoformat(),
        )


@dataclass(frozen=True, slots=True)
class FeatureDocumentationMapItemDto:
    document_type: str
    requirement: str
    coverage_status: str
    document_id: str | None
    policy_key: str
    created_at: str
    updated_at: str

    @classmethod
    def from_domain(
        cls,
        item: FeatureDocumentationMapItem,
    ) -> "FeatureDocumentationMapItemDto":
        return cls(
            document_type=item.document_type.value,
            requirement=item.requirement.value,
            coverage_status=item.coverage_status.value,
            document_id=item.document_id,
            policy_key=item.policy_key,
            created_at=item.created_at.isoformat(),
            updated_at=item.updated_at.isoformat(),
        )
