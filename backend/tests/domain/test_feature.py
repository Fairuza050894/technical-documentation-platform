from tdp.modules.features.domain.model import (
    DocumentationCoverageStatus,
    DocumentationRequirement,
    DocumentationType,
    Feature,
    FeatureDescription,
    FeatureKey,
    FeatureKind,
    FeatureName,
    FeatureOwner,
    FeatureStatus,
    create_documentation_map,
)

PROJECT_ID = "11111111-1111-4111-8111-111111111111"


def feature(kind: FeatureKind = FeatureKind.FEATURE) -> Feature:
    return Feature.create(
        project_id=PROJECT_ID,
        key=FeatureKey("PAYMENT"),
        name=FeatureName("Payment Processing"),
        description=FeatureDescription("Payment capture and verification."),
        kind=kind,
        owner=FeatureOwner("ERP Team"),
    )


def test_feature_normalizes_identity_and_archives() -> None:
    item = feature()

    assert str(item.key) == "PAYMENT"
    assert str(item.owner) == "ERP Team"
    assert item.status is FeatureStatus.ACTIVE

    item.archive()

    assert item.status is FeatureStatus.ARCHIVED


def test_documentation_baseline_is_deterministic_by_feature_kind() -> None:
    feature_items = create_documentation_map(feature(FeatureKind.FEATURE))
    module_items = create_documentation_map(feature(FeatureKind.MODULE))

    assert len(feature_items) == len(DocumentationType)
    assert len(module_items) == len(DocumentationType)
    assert all(item.policy_key == "feature-documentation-baseline-v1" for item in feature_items)

    feature_required = {
        item.document_type
        for item in feature_items
        if item.requirement is DocumentationRequirement.REQUIRED
    }
    module_required = {
        item.document_type
        for item in module_items
        if item.requirement is DocumentationRequirement.REQUIRED
    }

    assert DocumentationType.BUSINESS_REQUIREMENT in feature_required
    assert DocumentationType.API_DOCUMENTATION not in feature_required
    assert DocumentationType.API_DOCUMENTATION in module_required
    assert DocumentationType.DATABASE_SPECIFICATION in module_required
    assert all(
        item.coverage_status
        in {DocumentationCoverageStatus.MISSING, DocumentationCoverageStatus.PLANNED}
        for item in feature_items
    )
