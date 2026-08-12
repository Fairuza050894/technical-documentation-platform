from tdp.modules.readiness.domain.model import (
    DocumentReadinessProfile,
    ReadinessFindingSeverity,
    ReadinessRule,
    ReadinessRuleKind,
)

READINESS_POLICY_VERSION = "document-readiness-v2"

_HLD = DocumentReadinessProfile(
    document_type="HLD",
    rules=(
        ReadinessRule(
            code="HLD_TECHNICAL_EVIDENCE_REQUIRED",
            kind=ReadinessRuleKind.EVIDENCE_KIND_ANY_OF,
            severity=ReadinessFindingSeverity.BLOCKER,
            message="High Level Design requires traceable technical boundary evidence.",
            missing_input="technical-evidence",
            remediation="Register validated source or normalized technical evidence.",
            evidence_kinds=("SOURCE_ARTIFACT", "CATALOG_SNAPSHOT"),
        ),
        ReadinessRule(
            code="HLD_GOVERNED_CONTEXT_REQUIRED",
            kind=ReadinessRuleKind.RELEVANT_CLAIM,
            severity=ReadinessFindingSeverity.WARNING,
            message="Architecture context or rationale has not been captured as a governed claim.",
            missing_input="governed-hld-context",
            remediation=(
                "Add an observed or deterministically inferred HLD-relevant claim; "
                "do not infer architecture decisions from implementation artifacts alone."
            ),
            allowed_claim_classifications=("OBSERVED", "INFERRED"),
        ),
    ),
)

_LLD = DocumentReadinessProfile(
    document_type="LLD",
    rules=(
        ReadinessRule(
            code="LLD_NORMALIZED_TECHNICAL_EVIDENCE_REQUIRED",
            kind=ReadinessRuleKind.EVIDENCE_KIND,
            severity=ReadinessFindingSeverity.BLOCKER,
            message="Low Level Design requires normalized implementation-level technical evidence.",
            missing_input="evidence-kind:CATALOG_SNAPSHOT",
            remediation="Register a completed normalized API Catalog snapshot as evidence.",
            evidence_kind="CATALOG_SNAPSHOT",
        ),
        ReadinessRule(
            code="LLD_GOVERNED_CONTEXT_RECOMMENDED",
            kind=ReadinessRuleKind.RELEVANT_CLAIM,
            severity=ReadinessFindingSeverity.WARNING,
            message="Implementation context is not yet represented by a governed LLD claim.",
            missing_input="governed-lld-context",
            remediation="Add an observed or deterministically inferred LLD-relevant claim.",
            allowed_claim_classifications=("OBSERVED", "INFERRED"),
        ),
    ),
)

_AS_BUILT = DocumentReadinessProfile(
    document_type="AS_BUILT",
    rules=(
        ReadinessRule(
            code="ASBUILT_IMPLEMENTATION_EVIDENCE_REQUIRED",
            kind=ReadinessRuleKind.EVIDENCE_KIND,
            severity=ReadinessFindingSeverity.BLOCKER,
            message="As-Built documentation requires direct normalized implementation evidence.",
            missing_input="evidence-kind:CATALOG_SNAPSHOT",
            remediation="Register a completed normalized implementation snapshot as evidence.",
            evidence_kind="CATALOG_SNAPSHOT",
        ),
        ReadinessRule(
            code="ASBUILT_OBSERVED_CLAIM_REQUIRED",
            kind=ReadinessRuleKind.RELEVANT_CLAIM,
            severity=ReadinessFindingSeverity.BLOCKER,
            message="As-Built factual statements require at least one observed governed claim.",
            missing_input="observed-as-built-claim",
            remediation="Add an OBSERVED As-Built claim backed by persisted evidence.",
            allowed_claim_classifications=("OBSERVED",),
        ),
    ),
)

_SOP = DocumentReadinessProfile(
    document_type="SOP",
    rules=(
        ReadinessRule(
            code="SOP_VALIDATED_OPERATIONAL_CLAIM_REQUIRED",
            kind=ReadinessRuleKind.RELEVANT_CLAIM,
            severity=ReadinessFindingSeverity.BLOCKER,
            message="SOP drafting requires validated operational procedure input.",
            missing_input="observed-sop-claim",
            remediation=(
                "Capture an OBSERVED SOP-relevant operational claim backed by evidence; "
                "do not fabricate procedures from technical evidence."
            ),
            allowed_claim_classifications=("OBSERVED",),
        ),
    ),
)

_USER_GUIDE = DocumentReadinessProfile(
    document_type="USER_GUIDE",
    rules=(
        ReadinessRule(
            code="USER_GUIDE_JOURNEY_EVIDENCE_REQUIRED",
            kind=ReadinessRuleKind.EVIDENCE_KIND,
            severity=ReadinessFindingSeverity.BLOCKER,
            message="User Guide drafting requires validated user-journey evidence.",
            missing_input="evidence-kind:USER_JOURNEY",
            remediation="Capture validated user-facing journey evidence before governed drafting.",
            evidence_kind="USER_JOURNEY",
        ),
        ReadinessRule(
            code="USER_GUIDE_GOVERNED_CLAIM_RECOMMENDED",
            kind=ReadinessRuleKind.RELEVANT_CLAIM,
            severity=ReadinessFindingSeverity.WARNING,
            message="No observed user-facing claim is mapped to the User Guide.",
            missing_input="observed-user-guide-claim",
            remediation="Add an OBSERVED User Guide claim when journey evidence is available.",
            allowed_claim_classifications=("OBSERVED",),
        ),
    ),
)

_INSTALLATION_GUIDE = DocumentReadinessProfile(
    document_type="INSTALLATION_GUIDE",
    rules=(
        ReadinessRule(
            code="INSTALLATION_DEPLOYMENT_EVIDENCE_REQUIRED",
            kind=ReadinessRuleKind.EVIDENCE_KIND,
            severity=ReadinessFindingSeverity.BLOCKER,
            message="Installation Guide drafting requires deployment or runtime evidence.",
            missing_input="evidence-kind:DEPLOYMENT_RUNTIME",
            remediation=(
                "Add validated CI/CD, IaC, container, environment, runtime, or deployment evidence."
            ),
            evidence_kind="DEPLOYMENT_RUNTIME",
        ),
    ),
)

_PROJECT_HANDOVER = DocumentReadinessProfile(
    document_type="PROJECT_HANDOVER",
    rules=(
        ReadinessRule(
            code="HANDOVER_REQUIRED_DOCUMENTS_APPROVED",
            kind=ReadinessRuleKind.APPROVED_DOCUMENTS,
            severity=ReadinessFindingSeverity.BLOCKER,
            message="Project Handover requires approved versions of the required document bundle.",
            missing_input="approved-required-documents",
            remediation=(
                "Create, review, and approve HLD, LLD, As-Built, SOP, User Guide, "
                "and Installation Guide before handover."
            ),
            required_document_types=(
                "HLD",
                "LLD",
                "AS_BUILT",
                "SOP",
                "USER_GUIDE",
                "INSTALLATION_GUIDE",
            ),
        ),
    ),
)

_UAT_EVIDENCE = DocumentReadinessProfile(
    document_type="UAT_EVIDENCE",
    rules=(
        ReadinessRule(
            code="UAT_EXECUTION_EVIDENCE_REQUIRED",
            kind=ReadinessRuleKind.EVIDENCE_KIND,
            severity=ReadinessFindingSeverity.BLOCKER,
            message="UAT Evidence requires traceable acceptance-test execution evidence.",
            missing_input="evidence-kind:UAT_RESULT",
            remediation=(
                "Capture governed UAT scenarios, execution results, and supporting evidence."
            ),
            evidence_kind="UAT_RESULT",
        ),
    ),
)

_JOURNEY_MAP = DocumentReadinessProfile(
    document_type="JOURNEY_MAP",
    rules=(
        ReadinessRule(
            code="JOURNEY_OBSERVATION_EVIDENCE_REQUIRED",
            kind=ReadinessRuleKind.EVIDENCE_KIND,
            severity=ReadinessFindingSeverity.BLOCKER,
            message="Journey Map generation requires observed or validated journey evidence.",
            missing_input="evidence-kind:USER_JOURNEY",
            remediation="Capture a validated user/system journey before generating a Journey Map.",
            evidence_kind="USER_JOURNEY",
        ),
    ),
)

_DEVELOPER_ONBOARDING = DocumentReadinessProfile(
    document_type="DEVELOPER_ONBOARDING_BRIEF",
    rules=(
        ReadinessRule(
            code="ONBOARDING_TECHNICAL_EVIDENCE_REQUIRED",
            kind=ReadinessRuleKind.EVIDENCE_KIND_ANY_OF,
            severity=ReadinessFindingSeverity.BLOCKER,
            message="Developer onboarding requires traceable technical evidence.",
            missing_input="technical-evidence",
            remediation="Register validated source or normalized technical evidence.",
            evidence_kinds=("SOURCE_ARTIFACT", "CATALOG_SNAPSHOT"),
        ),
        ReadinessRule(
            code="ONBOARDING_GOVERNED_CONTEXT_REQUIRED",
            kind=ReadinessRuleKind.RELEVANT_CLAIM,
            severity=ReadinessFindingSeverity.WARNING,
            message="Developer onboarding context has not been captured as a governed claim.",
            missing_input="governed-onboarding-context",
            remediation=(
                "Add an observed or deterministically inferred onboarding-relevant "
                "contextual claim."
            ),
            allowed_claim_classifications=("OBSERVED", "INFERRED"),
        ),
    ),
)

READINESS_PROFILES: tuple[DocumentReadinessProfile, ...] = (
    _HLD,
    _LLD,
    _AS_BUILT,
    _SOP,
    _USER_GUIDE,
    _INSTALLATION_GUIDE,
    _PROJECT_HANDOVER,
    _UAT_EVIDENCE,
    _JOURNEY_MAP,
    _DEVELOPER_ONBOARDING,
)

_PROFILE_BY_TYPE = {profile.document_type: profile for profile in READINESS_PROFILES}


def readiness_profile(document_type: str) -> DocumentReadinessProfile:
    return _PROFILE_BY_TYPE[document_type]
