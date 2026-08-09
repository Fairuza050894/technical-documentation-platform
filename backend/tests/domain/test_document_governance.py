from tdp.modules.documents.domain.governance import (
    DOCUMENT_TYPE_REGISTRY,
    PROJECT_DOCUMENTATION_POLICY,
    AutomationProfile,
    ProjectDocumentRequirement,
)
from tdp.modules.documents.domain.model import DocumentType


def test_enterprise_document_registry_has_stable_identity_order_and_profiles() -> None:
    assert [item.document_type for item in DOCUMENT_TYPE_REGISTRY] == [
        DocumentType.HLD,
        DocumentType.LLD,
        DocumentType.AS_BUILT,
        DocumentType.SOP,
        DocumentType.USER_GUIDE,
        DocumentType.INSTALLATION_GUIDE,
        DocumentType.PROJECT_HANDOVER,
        DocumentType.UAT_EVIDENCE,
        DocumentType.JOURNEY_MAP,
        DocumentType.DEVELOPER_ONBOARDING_BRIEF,
    ]
    assert [item.order for item in DOCUMENT_TYPE_REGISTRY] == list(range(1, 11))
    assert len({item.document_type for item in DOCUMENT_TYPE_REGISTRY}) == 10

    profiles = {item.document_type: item.automation_profile for item in DOCUMENT_TYPE_REGISTRY}
    assert profiles == {
        DocumentType.HLD: AutomationProfile.HYBRID,
        DocumentType.LLD: AutomationProfile.EVIDENCE_DRIVEN,
        DocumentType.AS_BUILT: AutomationProfile.EVIDENCE_DRIVEN,
        DocumentType.SOP: AutomationProfile.GOVERNED_AUTHORING,
        DocumentType.USER_GUIDE: AutomationProfile.GOVERNED_AUTHORING,
        DocumentType.INSTALLATION_GUIDE: AutomationProfile.EVIDENCE_DRIVEN,
        DocumentType.PROJECT_HANDOVER: AutomationProfile.GOVERNED_BUNDLE,
        DocumentType.UAT_EVIDENCE: AutomationProfile.EVIDENCE_DRIVEN,
        DocumentType.JOURNEY_MAP: AutomationProfile.EVIDENCE_DRIVEN,
        DocumentType.DEVELOPER_ONBOARDING_BRIEF: AutomationProfile.HYBRID,
    }


def test_project_documentation_policy_has_seven_required_and_three_supplementary_items() -> None:
    required = [
        item.document_type
        for item in PROJECT_DOCUMENTATION_POLICY
        if item.requirement is ProjectDocumentRequirement.REQUIRED
    ]
    supplementary = [
        item.document_type
        for item in PROJECT_DOCUMENTATION_POLICY
        if item.requirement is ProjectDocumentRequirement.SUPPLEMENTARY
    ]

    assert required == [
        DocumentType.HLD,
        DocumentType.LLD,
        DocumentType.AS_BUILT,
        DocumentType.SOP,
        DocumentType.USER_GUIDE,
        DocumentType.INSTALLATION_GUIDE,
        DocumentType.PROJECT_HANDOVER,
    ]
    assert supplementary == [
        DocumentType.UAT_EVIDENCE,
        DocumentType.JOURNEY_MAP,
        DocumentType.DEVELOPER_ONBOARDING_BRIEF,
    ]


def test_technical_source_overview_is_excluded_from_enterprise_checklist() -> None:
    registered_types = {item.document_type for item in DOCUMENT_TYPE_REGISTRY}
    policy_types = {item.document_type for item in PROJECT_DOCUMENTATION_POLICY}

    assert DocumentType.TECHNICAL_SOURCE_OVERVIEW not in registered_types
    assert DocumentType.TECHNICAL_SOURCE_OVERVIEW not in policy_types
