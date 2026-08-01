from typing import Annotated, cast

from fastapi import Depends, Request

from tdp.identity.model import RequestPrincipal
from tdp.identity.provider import IdentityProvider


def get_request_principal(request: Request) -> RequestPrincipal:
    provider = cast(IdentityProvider, request.app.state.identity_provider)
    return provider.current_principal()


PrincipalDependency = Annotated[RequestPrincipal, Depends(get_request_principal)]
