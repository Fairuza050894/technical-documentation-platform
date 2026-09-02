from tdp.modules.scanner.domain.webhook import (
    WebhookEvent,
    WebhookEventId,
    WebhookEventType,
    WebhookStatus,
)


class TestWebhookEventId:
    def test_new_generates_unique_ids(self) -> None:
        first = WebhookEventId.new()
        second = WebhookEventId.new()
        assert str(first) != str(second)

    def test_from_string_roundtrip(self) -> None:
        event_id = WebhookEventId.new()
        restored = WebhookEventId.from_string(str(event_id))
        assert str(event_id) == str(restored)


class TestWebhookEventCreate:
    def test_create_sets_correct_fields(self) -> None:
        event = WebhookEvent.create(
            event_type=WebhookEventType.PUSH,
            repository_url="https://github.com/org/repo.git",
            repository_name="repo",
            branch="main",
            commit_sha="abc123",
            commit_message="fix: bug",
            sender="user1",
        )
        assert event.event_type == WebhookEventType.PUSH
        assert event.repository_url == "https://github.com/org/repo.git"
        assert event.repository_name == "repo"
        assert event.branch == "main"
        assert event.commit_sha == "abc123"
        assert event.commit_message == "fix: bug"
        assert event.sender == "user1"
        assert event.status == WebhookStatus.PENDING
        assert event.scan_id == ""
        assert event.processed_at is None

    def test_create_pr_event(self) -> None:
        event = WebhookEvent.create(
            event_type=WebhookEventType.PULL_REQUEST,
            repository_url="https://github.com/org/repo.git",
            repository_name="repo",
            branch="feature-branch",
            commit_sha="def456",
            commit_message="Add new feature",
            sender="dev2",
        )
        assert event.event_type == WebhookEventType.PULL_REQUEST
        assert event.branch == "feature-branch"


class TestWebhookEventLifecycle:
    def test_mark_processing(self) -> None:
        event = WebhookEvent.create(
            WebhookEventType.PUSH, "url", "name", "main", "sha", "msg", "user"
        )
        event.mark_processing()
        assert event.status == WebhookStatus.PROCESSING

    def test_mark_completed(self) -> None:
        event = WebhookEvent.create(
            WebhookEventType.PUSH, "url", "name", "main", "sha", "msg", "user"
        )
        event.mark_completed(scan_id="scan-1", previous_scan_id="", score_delta=5)
        assert event.status == WebhookStatus.COMPLETED
        assert event.scan_id == "scan-1"
        assert event.score_delta == 5
        assert event.processed_at is not None

    def test_mark_failed(self) -> None:
        event = WebhookEvent.create(
            WebhookEventType.PUSH, "url", "name", "main", "sha", "msg", "user"
        )
        event.mark_failed("clone failed")
        assert event.status == WebhookStatus.FAILED
        assert event.error_message == "clone failed"
        assert event.processed_at is not None

    def test_mark_skipped(self) -> None:
        event = WebhookEvent.create(
            WebhookEventType.PULL_REQUEST, "url", "name", "main", "sha", "msg", "user"
        )
        event.mark_skipped("PR action 'closed' ignored")
        assert event.status == WebhookStatus.SKIPPED
        assert "ignored" in event.error_message
