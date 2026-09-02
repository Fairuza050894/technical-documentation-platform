import hashlib
import hmac
import json
from dataclasses import dataclass

from tdp.modules.scanner.application.service import ScannerApplicationService
from tdp.modules.scanner.domain.webhook import (
    WebhookEvent,
    WebhookEventId,
    WebhookEventType,
)
from tdp.modules.scanner.domain.webhook_repository import WebhookRepository


class WebhookSignatureError(Exception):
    pass


class WebhookEventNotFoundError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class WebhookEventDto:
    id: str
    event_type: str
    repository_url: str
    repository_name: str
    branch: str
    commit_sha: str
    commit_message: str
    sender: str
    status: str
    scan_id: str
    previous_scan_id: str
    score_delta: int
    error_message: str
    created_at: str
    processed_at: str | None

    @classmethod
    def from_domain(cls, event: WebhookEvent) -> "WebhookEventDto":
        return cls(
            id=str(event.id),
            event_type=event.event_type.value,
            repository_url=event.repository_url,
            repository_name=event.repository_name,
            branch=event.branch,
            commit_sha=event.commit_sha,
            commit_message=event.commit_message,
            sender=event.sender,
            status=event.status.value,
            scan_id=event.scan_id,
            previous_scan_id=event.previous_scan_id,
            score_delta=event.score_delta,
            error_message=event.error_message,
            created_at=event.created_at.isoformat(),
            processed_at=event.processed_at.isoformat() if event.processed_at else None,
        )


class WebhookApplicationService:
    def __init__(
        self,
        webhook_repository: WebhookRepository,
        scanner_service: ScannerApplicationService,
        webhook_secret: str = "",
    ) -> None:
        self._repository = webhook_repository
        self._scanner_service = scanner_service
        self._webhook_secret = webhook_secret

    async def process_github_push(self, payload: dict, signature: str = "") -> WebhookEventDto:
        if self._webhook_secret and signature:
            self._verify_signature(payload, signature)

        repository = payload.get("repository", {})
        repo_url = repository.get("clone_url", "")
        repo_name = repository.get("name", "")
        ref = payload.get("ref", "")
        branch = ref.replace("refs/heads/", "")
        head_commit = payload.get("head_commit", {}) or {}
        commit_sha = head_commit.get("id", payload.get("after", ""))
        commit_message = head_commit.get("message", "")
        sender = payload.get("sender", {}).get("login", "")

        event = WebhookEvent.create(
            event_type=WebhookEventType.PUSH,
            repository_url=repo_url,
            repository_name=repo_name,
            branch=branch,
            commit_sha=commit_sha,
            commit_message=commit_message[:200],
            sender=sender,
        )

        await self._repository.save(event)
        return await self._process_event(event)

    async def process_github_pr(self, payload: dict, signature: str = "") -> WebhookEventDto:
        if self._webhook_secret and signature:
            self._verify_signature(payload, signature)

        action = payload.get("action", "")
        if action not in ("opened", "synchronize", "reopened"):
            event = WebhookEvent.create(
                event_type=WebhookEventType.PULL_REQUEST,
                repository_url=payload.get("repository", {}).get("clone_url", ""),
                repository_name=payload.get("repository", {}).get("name", ""),
                branch=payload.get("pull_request", {}).get("head", {}).get("ref", ""),
                commit_sha=payload.get("pull_request", {}).get("head", {}).get("sha", ""),
                commit_message=f"PR {action}",
                sender=payload.get("sender", {}).get("login", ""),
            )
            event.mark_skipped(f"PR action '{action}' ignored")
            await self._repository.save(event)
            return WebhookEventDto.from_domain(event)

        pr = payload.get("pull_request", {})
        repository = payload.get("repository", {})
        head = pr.get("head", {})

        event = WebhookEvent.create(
            event_type=WebhookEventType.PULL_REQUEST,
            repository_url=repository.get("clone_url", ""),
            repository_name=repository.get("name", ""),
            branch=head.get("ref", ""),
            commit_sha=head.get("sha", ""),
            commit_message=pr.get("title", ""),
            sender=payload.get("sender", {}).get("login", ""),
        )

        await self._repository.save(event)
        return await self._process_event(event)

    async def get_event(self, event_id: str) -> WebhookEventDto:
        event = await self._repository.get(WebhookEventId.from_string(event_id))
        if event is None:
            raise WebhookEventNotFoundError(f"Webhook event {event_id} not found.")
        return WebhookEventDto.from_domain(event)

    async def list_events(self, limit: int = 50) -> list[WebhookEventDto]:
        events = await self._repository.list_all(limit)
        return [WebhookEventDto.from_domain(e) for e in events]

    async def list_events_by_repo(self, repository_url: str, limit: int = 20) -> list[WebhookEventDto]:
        events = await self._repository.list_by_repo(repository_url, limit)
        return [WebhookEventDto.from_domain(e) for e in events]

    async def _process_event(self, event: WebhookEvent) -> WebhookEventDto:
        try:
            event.mark_processing()
            await self._repository.save(event)

            # Find previous scan for this repo+branch
            previous_scan_id = ""
            score_delta = 0
            all_scans = await self._scanner_service.list_scans()
            for scan in all_scans:
                if (scan.repository_url == event.repository_url
                        and scan.branch == event.branch
                        and scan.status == "COMPLETED"):
                    previous_scan_id = scan.id
                    break

            # Start new scan
            scan_dto = await self._scanner_service.start_scan(
                event.repository_url, event.branch
            )

            event.mark_completed(
                scan_id=scan_dto.id,
                previous_scan_id=previous_scan_id,
                score_delta=score_delta,
            )
            await self._repository.save(event)

        except Exception as exc:
            event.mark_failed(str(exc))
            await self._repository.save(event)

        return WebhookEventDto.from_domain(event)

    def _verify_signature(self, payload: dict, signature: str) -> None:
        if not signature.startswith("sha256="):
            raise WebhookSignatureError("Invalid signature format.")
        expected = hmac.new(
            self._webhook_secret.encode(),
            json.dumps(payload, separators=(",", ":")).encode(),
            hashlib.sha256,
        ).hexdigest()
        provided = signature[7:]
        if not hmac.compare_digest(expected, provided):
            raise WebhookSignatureError("Signature mismatch.")
