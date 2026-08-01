from typing import Self

from fastapi import APIRouter, Response
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

    @classmethod
    def from_principal(cls, principal: RequestPrincipal) -> Self:
        return cls(
            subject_id=principal.subject_id,
            display_name=principal.display_name,
            email=principal.email,
            provider=principal.provider,
            assurance=principal.assurance.value,
            audit_actor=principal.audit_actor,
        )


@router.get("/me", response_model=CurrentIdentityResponse)
async def get_current_identity(
    principal: PrincipalDependency,
    response: Response,
) -> CurrentIdentityResponse:
    response.headers["Cache-Control"] = "no-store"
    return CurrentIdentityResponse.from_principal(principal)
