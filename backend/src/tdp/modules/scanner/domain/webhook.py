from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class WebhookEventType(StrEnum):
    PUSH = "push"
    PULL_REQUEST = "pull_request"


class WebhookStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True, slots=True)
class WebhookEventId:
    value: UUID

    @classmethod
    def new(cls) -> "WebhookEventId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "WebhookEventId":
        return cls(UUID(value))

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class WebhookEvent:
    id: WebhookEventId
    event_type: WebhookEventType
    repository_url: str
    repository_name: str
    branch: str
    commit_sha: str
    commit_message: str
    sender: str
    status: WebhookStatus
    scan_id: str
    previous_scan_id: str
    score_delta: int
    error_message: str
    created_at: datetime
    processed_at: datetime | None

    @classmethod
    def create(
        cls,
        event_type: WebhookEventType,
        repository_url: str,
        repository_name: str,
        branch: str,
        commit_sha: str,
        commit_message: str,
        sender: str,
    ) -> "WebhookEvent":
        return cls(
            id=WebhookEventId.new(),
            event_type=event_type,
            repository_url=repository_url,
            repository_name=repository_name,
            branch=branch,
            commit_sha=commit_sha,
            commit_message=commit_message,
            sender=sender,
            status=WebhookStatus.PENDING,
            scan_id="",
            previous_scan_id="",
            score_delta=0,
            error_message="",
            created_at=datetime.now(UTC),
            processed_at=None,
        )

    def mark_processing(self) -> None:
        self.status = WebhookStatus.PROCESSING

    def mark_completed(self, scan_id: str, previous_scan_id: str, score_delta: int) -> None:
        self.status = WebhookStatus.COMPLETED
        self.scan_id = scan_id
        self.previous_scan_id = previous_scan_id
        self.score_delta = score_delta
        self.processed_at = datetime.now(UTC)

    def mark_failed(self, error: str) -> None:
        self.status = WebhookStatus.FAILED
        self.error_message = error
        self.processed_at = datetime.now(UTC)

    def mark_skipped(self, reason: str) -> None:
        self.status = WebhookStatus.SKIPPED
        self.error_message = reason
        self.processed_at = datetime.now(UTC)
