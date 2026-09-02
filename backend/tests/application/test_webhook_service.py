import pytest

from tdp.modules.scanner.application.service import ScannerApplicationService
from tdp.modules.scanner.application.webhook_service import (
    WebhookApplicationService,
    WebhookEventNotFoundError,
    WebhookSignatureError,
)
from tdp.modules.scanner.domain.model import ScanResult
from tdp.modules.scanner.domain.webhook import WebhookEvent, WebhookEventType, WebhookStatus
from tdp.modules.scanner.domain.webhook_repository import WebhookRepository


class InMemoryWebhookRepository:
    def __init__(self) -> None:
        self._events: dict[str, WebhookEvent] = {}

    async def save(self, event: WebhookEvent) -> None:
        self._events[str(event.id)] = event

    async def get(self, event_id) -> WebhookEvent | None:
        return self._events.get(str(event_id))

    async def list_all(self, limit: int = 50) -> list[WebhookEvent]:
        return sorted(
            self._events.values(),
            key=lambda e: e.created_at,
            reverse=True,
        )[:limit]

    async def list_by_repo(self, repository_url: str, limit: int = 20) -> list[WebhookEvent]:
        return [
            e for e in self._events.values()
            if e.repository_url == repository_url
        ][:limit]


class InMemoryScanRepository:
    def __init__(self) -> None:
        self._scans: dict[str, ScanResult] = {}

    async def save(self, scan: ScanResult) -> None:
        self._scans[str(scan.id)] = scan

    async def get(self, scan_id):
        return self._scans.get(str(scan_id))

    async def list_all(self) -> list[ScanResult]:
        return sorted(
            self._scans.values(),
            key=lambda s: s.started_at,
            reverse=True,
        )

    async def delete(self, scan_id) -> bool:
        key = str(scan_id)
        if key in self._scans:
            del self._scans[key]
            return True
        return False


def _make_push_payload(
    repo_url="https://github.com/org/repo.git",
    repo_name="repo",
    branch="main",
    sha="abc123",
    message="test commit",
    sender="user1",
) -> dict:
    return {
        "ref": f"refs/heads/{branch}",
        "after": sha,
        "head_commit": {"id": sha, "message": message},
        "repository": {"clone_url": repo_url, "name": repo_name},
        "sender": {"login": sender},
    }


def _make_pr_payload(
    action="opened",
    repo_url="https://github.com/org/repo.git",
    repo_name="repo",
    branch="feature",
    sha="def456",
    title="Add feature",
    sender="dev1",
) -> dict:
    return {
        "action": action,
        "pull_request": {
            "title": title,
            "head": {"ref": branch, "sha": sha},
        },
        "repository": {"clone_url": repo_url, "name": repo_name},
        "sender": {"login": sender},
    }


class TestWebhookServicePush:
    @pytest.mark.asyncio
    async def test_process_push_creates_event(self) -> None:
        webhook_repo = InMemoryWebhookRepository()
        scan_repo = InMemoryScanRepository()
        scanner_service = ScannerApplicationService(scan_repo)
        service = WebhookApplicationService(webhook_repo, scanner_service)

        payload = _make_push_payload()
        result = await service.process_github_push(payload)

        assert result.event_type == "push"
        assert result.repository_name == "repo"
        assert result.branch == "main"
        assert result.commit_sha == "abc123"
        assert result.sender == "user1"
        assert result.status == "COMPLETED"
        assert result.scan_id != ""

    @pytest.mark.asyncio
    async def test_push_event_saved_to_repository(self) -> None:
        webhook_repo = InMemoryWebhookRepository()
        scan_repo = InMemoryScanRepository()
        scanner_service = ScannerApplicationService(scan_repo)
        service = WebhookApplicationService(webhook_repo, scanner_service)

        await service.process_github_push(_make_push_payload())

        events = await webhook_repo.list_all()
        assert len(events) == 1
        assert events[0].event_type == WebhookEventType.PUSH


class TestWebhookServicePR:
    @pytest.mark.asyncio
    async def test_process_pr_opened(self) -> None:
        webhook_repo = InMemoryWebhookRepository()
        scan_repo = InMemoryScanRepository()
        scanner_service = ScannerApplicationService(scan_repo)
        service = WebhookApplicationService(webhook_repo, scanner_service)

        payload = _make_pr_payload(action="opened")
        result = await service.process_github_pr(payload)

        assert result.event_type == "pull_request"
        assert result.status == "COMPLETED"
        assert result.scan_id != ""

    @pytest.mark.asyncio
    async def test_pr_closed_skipped(self) -> None:
        webhook_repo = InMemoryWebhookRepository()
        scan_repo = InMemoryScanRepository()
        scanner_service = ScannerApplicationService(scan_repo)
        service = WebhookApplicationService(webhook_repo, scanner_service)

        payload = _make_pr_payload(action="closed")
        result = await service.process_github_pr(payload)

        assert result.status == "SKIPPED"
        assert "ignored" in result.error_message

    @pytest.mark.asyncio
    async def test_pr_synchronize_processed(self) -> None:
        webhook_repo = InMemoryWebhookRepository()
        scan_repo = InMemoryScanRepository()
        scanner_service = ScannerApplicationService(scan_repo)
        service = WebhookApplicationService(webhook_repo, scanner_service)

        payload = _make_pr_payload(action="synchronize")
        result = await service.process_github_pr(payload)

        assert result.status == "COMPLETED"


class TestWebhookServiceList:
    @pytest.mark.asyncio
    async def test_list_events(self) -> None:
        webhook_repo = InMemoryWebhookRepository()
        scan_repo = InMemoryScanRepository()
        scanner_service = ScannerApplicationService(scan_repo)
        service = WebhookApplicationService(webhook_repo, scanner_service)

        await service.process_github_push(_make_push_payload())
        await service.process_github_push(_make_push_payload(sha="xyz789", message="second"))

        events = await service.list_events()
        assert len(events) == 2

    @pytest.mark.asyncio
    async def test_get_event(self) -> None:
        webhook_repo = InMemoryWebhookRepository()
        scan_repo = InMemoryScanRepository()
        scanner_service = ScannerApplicationService(scan_repo)
        service = WebhookApplicationService(webhook_repo, scanner_service)

        result = await service.process_github_push(_make_push_payload())
        fetched = await service.get_event(result.id)
        assert fetched.id == result.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_event_raises(self) -> None:
        webhook_repo = InMemoryWebhookRepository()
        scan_repo = InMemoryScanRepository()
        scanner_service = ScannerApplicationService(scan_repo)
        service = WebhookApplicationService(webhook_repo, scanner_service)

        with pytest.raises(WebhookEventNotFoundError):
            await service.get_event("00000000-0000-0000-0000-000000000000")


class TestWebhookSignature:
    @pytest.mark.asyncio
    async def test_invalid_signature_raises(self) -> None:
        webhook_repo = InMemoryWebhookRepository()
        scan_repo = InMemoryScanRepository()
        scanner_service = ScannerApplicationService(scan_repo)
        service = WebhookApplicationService(
            webhook_repo, scanner_service, webhook_secret="my-secret"
        )

        with pytest.raises(WebhookSignatureError):
            await service.process_github_push(
                _make_push_payload(), signature="sha256=invalid"
            )
