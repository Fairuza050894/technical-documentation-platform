import pytest

from tdp.identity.model import IdentityAssurance, RequestPrincipal


def test_request_principal_renders_stable_audit_actor() -> None:
    principal = RequestPrincipal(
        subject_id="local-technical-writer",
        display_name="  Technical   Writer ",
        email="Technical.Writer@Local.Invalid",
        provider="LOCAL",
        assurance=IdentityAssurance.DEVELOPMENT,
    )

    assert principal.display_name == "Technical Writer"
    assert principal.email == "technical.writer@local.invalid"
    assert principal.provider == "local"
    assert principal.audit_actor == "Technical Writer [local:local-technical-writer]"


def test_request_principal_rejects_an_oversized_audit_actor() -> None:
    with pytest.raises(ValueError, match="must not exceed 80"):
        RequestPrincipal(
            subject_id="subject-" + ("x" * 40),
            display_name="Identity " + ("y" * 39),
            email="identity@example.com",
            provider="development-provider",
            assurance=IdentityAssurance.DEVELOPMENT,
        )
