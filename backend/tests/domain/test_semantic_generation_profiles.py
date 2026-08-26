from tdp.modules.documents.domain.generation import enterprise_generation_profile
from tdp.modules.documents.domain.model import DocumentType


def test_semantic_generation_profiles_are_registered_as_one_coherent_pack() -> None:
    expected = {
        DocumentType.USER_GUIDE: (
            "enterprise-user-guide-v1",
            ("USER_JOURNEY",),
        ),
        DocumentType.INSTALLATION_GUIDE: (
            "enterprise-installation-guide-v1",
            ("DEPLOYMENT_RUNTIME",),
        ),
        DocumentType.UAT_EVIDENCE: (
            "enterprise-uat-evidence-v1",
            ("UAT_RESULT",),
        ),
        DocumentType.JOURNEY_MAP: (
            "enterprise-journey-map-v1",
            ("USER_JOURNEY",),
        ),
    }

    for document_type, (profile_key, evidence_kinds) in expected.items():
        profile = enterprise_generation_profile(document_type)
        assert profile is not None
        assert profile.profile_key == profile_key
        assert profile.accepted_evidence_kinds == evidence_kinds
        assert profile.rendered_claim_classifications == ()
