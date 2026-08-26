from typing import Annotated, cast

from fastapi import Depends, Request

from tdp.identity.model import RequestPrincipal
from tdp.identity.provider import IdentityProvider


def get_request_principal(request: Request) -> RequestPrincipal:
    # Check if JWT middleware already set the principal (OIDC mode)
    principal = getattr(request.state, "principal", None)
    if principal is not None:
        return principal

    # Fall back to identity provider (local mode)
    provider = cast(IdentityProvider, request.app.state.identity_provider)
    return provider.current_principal()


PrincipalDependency = Annotated[RequestPrincipal, Depends(get_request_principal)]