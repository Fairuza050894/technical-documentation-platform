from tdp.modules.readiness.domain.model import (
    DocumentReadinessProfile,
    ReadinessFindingSeverity,
    ReadinessRule,
    ReadinessRuleKind,
)

READINESS_POLICY_VERSION = "document-readiness-v3"

_HLD = DocumentReadinessProfile(
    document_type="HLD",
    rules=(
        ReadinessRule(
            code="HLD_TECHNICAL_EVIDENCE_REQUIRED",
            kind=ReadinessRuleKind.EVIDENCE_KIND_ANY_OF,
            severity=ReadinessFindingSeverity.BLOCKER,
            message="Add technical information that shows the system or solution boundary.",
            missing_input="technical-evidence",
            remediation=" ".join(
                (
                    "Add a technical source or completed API snapshot",
                    "that represents the solution.",
                )
            ),
            evidence_kinds=("SOURCE_ARTIFACT", "CATALOG_SNAPSHOT"),
        ),
        ReadinessRule(
            code="HLD_GOVERNED_CONTEXT_REQUIRED",
            kind=ReadinessRuleKind.RELEVANT_CLAIM,
            severity=ReadinessFindingSeverity.WARNING,
            message="Add the architecture context or reason behind the design.",
            missing_input="governed-hld-context",
            remediation="Add a confirmed note that explains the architecture context.",
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
            message="Add a completed API snapshot before preparing the Low Level Design.",
            missing_input="evidence-kind:CATALOG_SNAPSHOT",
            remediation="Create a completed API Catalog snapshot for this project.",
            evidence_kind="CATALOG_SNAPSHOT",
        ),
        ReadinessRule(
            code="LLD_GOVERNED_CONTEXT_RECOMMENDED",
            kind=ReadinessRuleKind.RELEVANT_CLAIM,
            severity=ReadinessFindingSeverity.WARNING,
            message="Add implementation context to make the Low Level Design more complete.",
            missing_input="governed-lld-context",
            remediation="Add a confirmed note about the implementation.",
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
            message=" ".join(
                (
                    "Add a completed implementation snapshot before preparing",
                    "the As-Built document.",
                )
            ),
            missing_input="evidence-kind:CATALOG_SNAPSHOT",
            remediation=" ".join(
                (
                    "Create a completed API Catalog snapshot that represents",
                    "the implemented system.",
                )
            ),
            evidence_kind="CATALOG_SNAPSHOT",
        ),
        ReadinessRule(
            code="ASBUILT_OBSERVED_CLAIM_REQUIRED",
            kind=ReadinessRuleKind.RELEVANT_CLAIM,
            severity=ReadinessFindingSeverity.BLOCKER,
            message="Add at least one confirmed fact about what is actually implemented.",
            missing_input="observed-as-built-claim",
            remediation="Add a confirmed As-Built fact linked to supporting evidence.",
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
            message="Add a confirmed operational procedure before preparing the SOP.",
            missing_input="observed-sop-claim",
            remediation=" ".join(
                (
                    "Add an operational step or procedure that has been",
                    "confirmed with evidence.",
                )
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
            kind=ReadinessRuleKind.MATERIALIZED_EVIDENCE_KIND,
            severity=ReadinessFindingSeverity.BLOCKER,
            message="Add a validated user journey before preparing the User Guide.",
            missing_input="evidence-kind:USER_JOURNEY",
            remediation="Add and validate the user journey that should be explained in this guide.",
            evidence_kind="USER_JOURNEY",
        ),
        ReadinessRule(
            code="USER_GUIDE_GOVERNED_CLAIM_RECOMMENDED",
            kind=ReadinessRuleKind.RELEVANT_CLAIM,
            severity=ReadinessFindingSeverity.WARNING,
            message="Add a confirmed user-facing note to make the User Guide clearer.",
            missing_input="observed-user-guide-claim",
            remediation="Describe what the user does or sees in the validated journey.",
            allowed_claim_classifications=("OBSERVED",),
        ),
    ),
)

_INSTALLATION_GUIDE = DocumentReadinessProfile(
    document_type="INSTALLATION_GUIDE",
    rules=(
        ReadinessRule(
            code="INSTALLATION_DEPLOYMENT_EVIDENCE_REQUIRED",
            kind=ReadinessRuleKind.MATERIALIZED_EVIDENCE_KIND,
            severity=ReadinessFindingSeverity.BLOCKER,
            message="Add deployment information before preparing the Installation Guide.",
            missing_input="evidence-kind:DEPLOYMENT_RUNTIME",
            remediation=" ".join(
                (
                    "Add and validate deployment or runtime information",
                    "for the target environment.",
                )
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
            message="Required project documents must be approved before handover.",
            missing_input="approved-required-documents",
            remediation="Complete review and approval for all required project documents.",
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
            kind=ReadinessRuleKind.MATERIALIZED_EVIDENCE_KIND,
            severity=ReadinessFindingSeverity.BLOCKER,
            message="Add completed UAT results before preparing UAT Evidence.",
            missing_input="evidence-kind:UAT_RESULT",
            remediation="Add and validate the UAT scenarios, results, and supporting evidence.",
            evidence_kind="UAT_RESULT",
        ),
    ),
)

_JOURNEY_MAP = DocumentReadinessProfile(
    document_type="JOURNEY_MAP",
    rules=(
        ReadinessRule(
            code="JOURNEY_OBSERVATION_EVIDENCE_REQUIRED",
            kind=ReadinessRuleKind.MATERIALIZED_EVIDENCE_KIND,
            severity=ReadinessFindingSeverity.BLOCKER,
            message="Add a validated user or system journey before preparing the Journey Map.",
            missing_input="evidence-kind:USER_JOURNEY",
            remediation="Add and validate the journey that should be represented in the map.",
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
            message="Add technical information that helps a new developer understand the project.",
            missing_input="technical-evidence",
            remediation="Add a technical source or completed API snapshot for the current system.",
            evidence_kinds=("SOURCE_ARTIFACT", "CATALOG_SNAPSHOT"),
        ),
        ReadinessRule(
            code="ONBOARDING_GOVERNED_CONTEXT_REQUIRED",
            kind=ReadinessRuleKind.RELEVANT_CLAIM,
            severity=ReadinessFindingSeverity.WARNING,
            message="Add project context that a new developer should know.",
            missing_input="governed-onboarding-context",
            remediation="Add a confirmed note about the project context and working assumptions.",
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
