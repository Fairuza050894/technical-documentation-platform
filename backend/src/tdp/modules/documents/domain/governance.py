from dataclasses import dataclass
from enum import StrEnum

from tdp.modules.documents.domain.model import DocumentType

DOCUMENT_TYPE_REGISTRY_SCHEMA_VERSION = "document-type-registry-v1"
PROJECT_DOCUMENTATION_POLICY_KEY = "project-documentation-baseline-v1"


class AutomationProfile(StrEnum):
    EVIDENCE_DRIVEN = "EVIDENCE_DRIVEN"
    HYBRID = "HYBRID"
    GOVERNED_AUTHORING = "GOVERNED_AUTHORING"
    GOVERNED_BUNDLE = "GOVERNED_BUNDLE"


class ProjectDocumentRequirement(StrEnum):
    REQUIRED = "REQUIRED"
    SUPPLEMENTARY = "SUPPLEMENTARY"


class ProjectDocumentAvailability(StrEnum):
    MISSING = "MISSING"
    AVAILABLE = "AVAILABLE"


@dataclass(frozen=True, slots=True)
class DocumentTypeDefinition:
    document_type: DocumentType
    display_name: str
    description: str
    automation_profile: AutomationProfile
    order: int


@dataclass(frozen=True, slots=True)
class ProjectDocumentationPolicyItem:
    document_type: DocumentType
    requirement: ProjectDocumentRequirement


DOCUMENT_TYPE_REGISTRY: tuple[DocumentTypeDefinition, ...] = (
    DocumentTypeDefinition(
        DocumentType.HLD,
        "High Level Design",
        "System boundaries, major components, integrations, and architecture rationale.",
        AutomationProfile.HYBRID,
        1,
    ),
    DocumentTypeDefinition(
        DocumentType.LLD,
        "Low Level Design",
        "Implementation-level components, interfaces, schemas, and technical contracts.",
        AutomationProfile.EVIDENCE_DRIVEN,
        2,
    ),
    DocumentTypeDefinition(
        DocumentType.AS_BUILT,
        "As-Built Documentation",
        "Verified representation of the system as actually implemented.",
        AutomationProfile.EVIDENCE_DRIVEN,
        3,
    ),
    DocumentTypeDefinition(
        DocumentType.SOP,
        "Standard Operating Procedure",
        "Governed operational procedures assembled from validated operational inputs.",
        AutomationProfile.GOVERNED_AUTHORING,
        4,
    ),
    DocumentTypeDefinition(
        DocumentType.USER_GUIDE,
        "User Guide",
        "Task-oriented guidance derived from validated features and user journeys.",
        AutomationProfile.GOVERNED_AUTHORING,
        5,
    ),
    DocumentTypeDefinition(
        DocumentType.INSTALLATION_GUIDE,
        "Installation Guide",
        "Installation, deployment, configuration, verification, and rollback guidance.",
        AutomationProfile.EVIDENCE_DRIVEN,
        6,
    ),
    DocumentTypeDefinition(
        DocumentType.PROJECT_HANDOVER,
        "Project Handover",
        "Governed project closeout package composed from eligible approved artifacts.",
        AutomationProfile.GOVERNED_BUNDLE,
        7,
    ),
    DocumentTypeDefinition(
        DocumentType.UAT_EVIDENCE,
        "UAT Evidence",
        "Traceable acceptance-test scenarios, execution results, and supporting evidence.",
        AutomationProfile.EVIDENCE_DRIVEN,
        8,
    ),
    DocumentTypeDefinition(
        DocumentType.JOURNEY_MAP,
        "Journey Map",
        "Observed or validated user and system journeys with traceable supporting evidence.",
        AutomationProfile.EVIDENCE_DRIVEN,
        9,
    ),
    DocumentTypeDefinition(
        DocumentType.DEVELOPER_ONBOARDING_BRIEF,
        "Developer Onboarding Brief",
        "Evidence-backed technical orientation with governed contextual guidance.",
        AutomationProfile.HYBRID,
        10,
    ),
)

PROJECT_DOCUMENTATION_POLICY: tuple[ProjectDocumentationPolicyItem, ...] = (
    ProjectDocumentationPolicyItem(DocumentType.HLD, ProjectDocumentRequirement.REQUIRED),
    ProjectDocumentationPolicyItem(DocumentType.LLD, ProjectDocumentRequirement.REQUIRED),
    ProjectDocumentationPolicyItem(DocumentType.AS_BUILT, ProjectDocumentRequirement.REQUIRED),
    ProjectDocumentationPolicyItem(DocumentType.SOP, ProjectDocumentRequirement.REQUIRED),
    ProjectDocumentationPolicyItem(DocumentType.USER_GUIDE, ProjectDocumentRequirement.REQUIRED),
    ProjectDocumentationPolicyItem(
        DocumentType.INSTALLATION_GUIDE,
        ProjectDocumentRequirement.REQUIRED,
    ),
    ProjectDocumentationPolicyItem(
        DocumentType.PROJECT_HANDOVER,
        ProjectDocumentRequirement.REQUIRED,
    ),
    ProjectDocumentationPolicyItem(
        DocumentType.UAT_EVIDENCE,
        ProjectDocumentRequirement.SUPPLEMENTARY,
    ),
    ProjectDocumentationPolicyItem(
        DocumentType.JOURNEY_MAP,
        ProjectDocumentRequirement.SUPPLEMENTARY,
    ),
    ProjectDocumentationPolicyItem(
        DocumentType.DEVELOPER_ONBOARDING_BRIEF,
        ProjectDocumentRequirement.SUPPLEMENTARY,
    ),
)

_DOCUMENT_TYPE_BY_ID = {item.document_type: item for item in DOCUMENT_TYPE_REGISTRY}


def document_type_definition(document_type: DocumentType) -> DocumentTypeDefinition:
    return _DOCUMENT_TYPE_BY_ID[document_type]
