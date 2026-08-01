from typing import Protocol

from tdp.identity.model import RequestPrincipal


class IdentityProvider(Protocol):
    def current_principal(self) -> RequestPrincipal: ...


class LocalIdentityProvider:
    def __init__(self, principal: RequestPrincipal) -> None:
        self._principal = principal

    def current_principal(self) -> RequestPrincipal:
        return self._principal
