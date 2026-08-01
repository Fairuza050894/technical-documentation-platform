from dataclasses import dataclass
from enum import StrEnum


class IdentityAssurance(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    VERIFIED = "VERIFIED"


@dataclass(frozen=True, slots=True)
class RequestPrincipal:
    subject_id: str
    display_name: str
    email: str
    provider: str
    assurance: IdentityAssurance

    def __post_init__(self) -> None:
        normalized_subject = self.subject_id.strip()
        normalized_name = " ".join(self.display_name.split())
        normalized_email = self.email.strip().casefold()
        normalized_provider = self.provider.strip().casefold()

        if not 2 <= len(normalized_subject) <= 48:
            raise ValueError("Principal subject ID must contain 2-48 characters.")
        if not 2 <= len(normalized_name) <= 48:
            raise ValueError("Principal display name must contain 2-48 characters.")
        if not 3 <= len(normalized_provider) <= 24:
            raise ValueError("Principal provider must contain 3-24 characters.")
        if normalized_email and ("@" not in normalized_email or len(normalized_email) > 254):
            raise ValueError("Principal email must be empty or a valid email address.")

        object.__setattr__(self, "subject_id", normalized_subject)
        object.__setattr__(self, "display_name", normalized_name)
        object.__setattr__(self, "email", normalized_email)
        object.__setattr__(self, "provider", normalized_provider)

        if len(self.audit_actor) > 80:
            raise ValueError("Rendered principal identity must not exceed 80 characters.")

    @property
    def audit_actor(self) -> str:
        return f"{self.display_name} [{self.provider}:{self.subject_id}]"
