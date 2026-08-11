from dataclasses import dataclass

from tdp.modules.documents.domain.model import DocumentType

ENTERPRISE_GENERATION_PROFILE_SCHEMA_VERSION = "enterprise-generation-profile-v1"


@dataclass(frozen=True, slots=True)
class GenerationReadinessFinding:
    rule_code: str
    severity: str
    message: str
    missing_input: str
    remediation: str
    supporting_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GenerationReadinessSnapshot:
    policy_version: str
    state: str
    eligible: bool
    findings: tuple[GenerationReadinessFinding, ...]


@dataclass(frozen=True, slots=True)
class EnterpriseDocumentGenerationProfile:
    profile_key: str
    document_type: DocumentType
    display_name: str
    file_slug: str
    primary_evidence_kind: str
    rendered_claim_classifications: tuple[str, ...]


_LLD_PROFILE = EnterpriseDocumentGenerationProfile(
    profile_key="enterprise-lld-v1",
    document_type=DocumentType.LLD,
    display_name="Low Level Design",
    file_slug="low-level-design",
    primary_evidence_kind="CATALOG_SNAPSHOT",
    rendered_claim_classifications=("OBSERVED", "INFERRED"),
)

_AS_BUILT_PROFILE = EnterpriseDocumentGenerationProfile(
    profile_key="enterprise-as-built-v1",
    document_type=DocumentType.AS_BUILT,
    display_name="As-Built Documentation",
    file_slug="as-built-documentation",
    primary_evidence_kind="CATALOG_SNAPSHOT",
    rendered_claim_classifications=("OBSERVED",),
)

ENTERPRISE_GENERATION_PROFILES: tuple[EnterpriseDocumentGenerationProfile, ...] = (
    _LLD_PROFILE,
    _AS_BUILT_PROFILE,
)

_PROFILE_BY_TYPE = {profile.document_type: profile for profile in ENTERPRISE_GENERATION_PROFILES}


def enterprise_generation_profile(
    document_type: DocumentType,
) -> EnterpriseDocumentGenerationProfile | None:
    return _PROFILE_BY_TYPE.get(document_type)
