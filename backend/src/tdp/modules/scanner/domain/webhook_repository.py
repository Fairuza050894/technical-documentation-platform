from abc import ABC, abstractmethod

from tdp.modules.scanner.domain.webhook import WebhookEvent, WebhookEventId


class WebhookRepository(ABC):
    @abstractmethod
    async def save(self, event: WebhookEvent) -> None: ...

    @abstractmethod
    async def get(self, event_id: WebhookEventId) -> WebhookEvent | None: ...

    @abstractmethod
    async def list_all(self, limit: int = 50) -> list[WebhookEvent]: ...

    @abstractmethod
    async def list_by_repo(self, repository_url: str, limit: int = 20) -> list[WebhookEvent]: ...
