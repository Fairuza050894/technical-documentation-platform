from typing import Self

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from tdp.identity.model import RequestPrincipal
from tdp.presentation.http.dependencies.identity import PrincipalDependency

router = APIRouter(prefix="/identity", tags=["identity"])


class CurrentIdentityResponse(BaseModel):
    subject_id: str
    display_name: str
    email: str
    provider: str
    assurance: str
    audit_actor: str
    role: str

    @classmethod
    def from_principal(cls, principal: RequestPrincipal, role: str) -> Self:
        return cls(
            subject_id=principal.subject_id,
            display_name=principal.display_name,
            email=principal.email,
            provider=principal.provider,
            assurance=principal.assurance.value,
            audit_actor=principal.audit_actor,
            role=role,
        )


def _resolve_role(request: Request, principal: RequestPrincipal) -> str:
    """Resolve the user's role from the authorization policy."""
    settings = getattr(request.app.state, "settings", None)

    # Check default admin subjects from settings
    if settings and hasattr(settings, "default_admin_subjects"):
        if principal.subject_id in settings.default_admin_subjects:
            return "admin"

    # Fallback: check authorization policy if available
    policy = getattr(request.app.state, "authorization_policy", None)
    if policy is not None:
        try:
            # Try common method names for admin check
            if hasattr(policy, "is_admin"):
                if policy.is_admin(principal.subject_id):
                    return "admin"
            elif hasattr(policy, "has_role"):
                if policy.has_role(principal.subject_id, "admin"):
                    return "admin"
            elif hasattr(policy, "check_admin"):
                if policy.check_admin(principal.subject_id):
                    return "admin"
        except Exception:
            pass

    return "viewer"


@router.get("/me", response_model=CurrentIdentityResponse)
async def get_current_identity(
    request: Request,
    principal: PrincipalDependency,
    response: Response,
) -> CurrentIdentityResponse:
    response.headers["Cache-Control"] = "no-store"
    role = _resolve_role(request, principal)
    return CurrentIdentityResponse.from_principal(principal, role)