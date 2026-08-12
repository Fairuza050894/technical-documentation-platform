import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from tdp.modules.documents.domain.errors import (
    InvalidDocumentActorError,
    InvalidDocumentCommentError,
    InvalidDocumentIdError,
    InvalidDocumentRevisionReasonError,
    InvalidDocumentVersionIdError,
    InvalidDocumentVersionNumberError,
    InvalidDocumentWorkflowTransitionError,
    InvalidWorkflowEventIdError,
)

_VERSION_PATTERN = re.compile(r"^(?P<major>[1-9][0-9]*)\.(?P<minor>0|[1-9][0-9]*)$")


class DocumentType(StrEnum):
    # Existing deterministic system artifact retained for backward compatibility.
    TECHNICAL_SOURCE_OVERVIEW = "TECHNICAL_SOURCE_OVERVIEW"

    # Canonical enterprise Project-level document types.
    HLD = "HLD"
    LLD = "LLD"
    AS_BUILT = "AS_BUILT"
    SOP = "SOP"
    USER_GUIDE = "USER_GUIDE"
    INSTALLATION_GUIDE = "INSTALLATION_GUIDE"
    PROJECT_HANDOVER = "PROJECT_HANDOVER"
    UAT_EVIDENCE = "UAT_EVIDENCE"
    JOURNEY_MAP = "JOURNEY_MAP"
    DEVELOPER_ONBOARDING_BRIEF = "DEVELOPER_ONBOARDING_BRIEF"


class DocumentFormat(StrEnum):
    MARKDOWN = "MARKDOWN"


class DocumentStatus(StrEnum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"
    SUPERSEDED = "SUPERSEDED"


class WorkflowAction(StrEnum):
    GENERATED = "GENERATED"
    SUBMITTED_FOR_REVIEW = "SUBMITTED_FOR_REVIEW"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True, slots=True)
class DocumentId:
    value: UUID

    @classmethod
    def new(cls) -> "DocumentId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "DocumentId":
        try:
            return cls(UUID(value))
        except ValueError as exc:
            raise InvalidDocumentIdError("Document ID must be a valid UUID.") from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class DocumentVersionId:
    value: UUID

    @classmethod
    def new(cls) -> "DocumentVersionId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "DocumentVersionId":
        try:
            return cls(UUID(value))
        except ValueError as exc:
            raise InvalidDocumentVersionIdError(
                "Document version ID must be a valid UUID."
            ) from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class WorkflowEventId:
    value: UUID

    @classmethod
    def new(cls) -> "WorkflowEventId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "WorkflowEventId":
        try:
            return cls(UUID(value))
        except ValueError as exc:
            raise InvalidWorkflowEventIdError("Workflow event ID must be a valid UUID.") from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class DocumentVersionNumber:
    major: int
    minor: int

    def __post_init__(self) -> None:
        if self.major < 1 or self.minor < 0:
            raise InvalidDocumentVersionNumberError(
                "Document version must use a positive major and non-negative minor number."
            )

    @classmethod
    def first(cls) -> "DocumentVersionNumber":
        return cls(major=1, minor=0)

    @classmethod
    def from_string(cls, value: str) -> "DocumentVersionNumber":
        match = _VERSION_PATTERN.fullmatch(value.strip())
        if match is None:
            raise InvalidDocumentVersionNumberError(
                "Document version must use major.minor format, for example 1.0."
            )
        return cls(major=int(match.group("major")), minor=int(match.group("minor")))

    def next_minor(self) -> "DocumentVersionNumber":
        return DocumentVersionNumber(major=self.major, minor=self.minor + 1)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"


@dataclass(slots=True)
class DocumentSeries:
    id: DocumentId
    project_id: str
    document_type: DocumentType
    title: str
    current_version_id: str | None
    current_approved_version_id: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        project_id: str,
        document_type: DocumentType,
        title: str,
        now: datetime | None = None,
    ) -> "DocumentSeries":
        timestamp = now or datetime.now(UTC)
        return cls(
            id=DocumentId.new(),
            project_id=project_id,
            document_type=document_type,
            title=title,
            current_version_id=None,
            current_approved_version_id=None,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def register_version(
        self,
        version_id: DocumentVersionId,
        *,
        now: datetime | None = None,
    ) -> None:
        self.current_version_id = str(version_id)
        self.updated_at = now or datetime.now(UTC)

    def register_approved_version(
        self,
        version_id: DocumentVersionId,
        *,
        now: datetime | None = None,
    ) -> None:
        self.current_approved_version_id = str(version_id)
        self.updated_at = now or datetime.now(UTC)

    def clear_approved_version(self, *, now: datetime | None = None) -> None:
        self.current_approved_version_id = None
        self.updated_at = now or datetime.now(UTC)


@dataclass(slots=True)
class DocumentVersion:
    id: DocumentVersionId
    document_id: DocumentId
    project_id: str
    source_id: str
    target_run_id: str | None
    baseline_run_id: str | None
    document_type: DocumentType
    document_format: DocumentFormat
    version_number: DocumentVersionNumber
    status: DocumentStatus
    title: str
    file_name: str
    content: str
    checksum: str
    operation_count: int
    schema_count: int
    breaking_change_count: int
    revision_reason: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None
    approved_at: datetime | None
    superseded_at: datetime | None

    @classmethod
    def create(
        cls,
        *,
        document_id: DocumentId,
        project_id: str,
        source_id: str,
        target_run_id: str | None,
        baseline_run_id: str | None,
        version_number: DocumentVersionNumber,
        title: str,
        file_name: str,
        content: str,
        operation_count: int,
        schema_count: int,
        breaking_change_count: int,
        revision_reason: str,
        created_by: str,
        document_type: DocumentType = DocumentType.TECHNICAL_SOURCE_OVERVIEW,
        now: datetime | None = None,
    ) -> "DocumentVersion":
        timestamp = now or datetime.now(UTC)
        return cls(
            id=DocumentVersionId.new(),
            document_id=document_id,
            project_id=project_id,
            source_id=source_id,
            target_run_id=target_run_id,
            baseline_run_id=baseline_run_id,
            document_type=document_type,
            document_format=DocumentFormat.MARKDOWN,
            version_number=version_number,
            status=DocumentStatus.DRAFT,
            title=title,
            file_name=file_name,
            content=content,
            checksum=hashlib.sha256(content.encode("utf-8")).hexdigest(),
            operation_count=operation_count,
            schema_count=schema_count,
            breaking_change_count=breaking_change_count,
            revision_reason=_revision_reason(revision_reason),
            created_by=_actor(created_by),
            created_at=timestamp,
            updated_at=timestamp,
            submitted_at=None,
            approved_at=None,
            superseded_at=None,
        )

    def generated_event(self) -> "DocumentWorkflowEvent":
        return DocumentWorkflowEvent.create(
            version_id=self.id,
            actor=self.created_by,
            action=WorkflowAction.GENERATED,
            previous_status=None,
            new_status=DocumentStatus.DRAFT,
            comment=self.revision_reason,
            now=self.created_at,
        )

    def submit_for_review(
        self,
        *,
        actor: str,
        comment: str = "",
        now: datetime | None = None,
    ) -> "DocumentWorkflowEvent":
        self._require_status(DocumentStatus.DRAFT, action="submit for review")
        timestamp = now or datetime.now(UTC)
        previous = self.status
        self.status = DocumentStatus.IN_REVIEW
        self.updated_at = timestamp
        self.submitted_at = timestamp
        return DocumentWorkflowEvent.create(
            version_id=self.id,
            actor=actor,
            action=WorkflowAction.SUBMITTED_FOR_REVIEW,
            previous_status=previous,
            new_status=self.status,
            comment=comment,
            now=timestamp,
        )

    def request_changes(
        self,
        *,
        actor: str,
        comment: str,
        now: datetime | None = None,
    ) -> "DocumentWorkflowEvent":
        self._require_status(DocumentStatus.IN_REVIEW, action="request changes")
        normalized_comment = _comment(comment, required=True)
        timestamp = now or datetime.now(UTC)
        previous = self.status
        self.status = DocumentStatus.CHANGES_REQUESTED
        self.updated_at = timestamp
        return DocumentWorkflowEvent.create(
            version_id=self.id,
            actor=actor,
            action=WorkflowAction.CHANGES_REQUESTED,
            previous_status=previous,
            new_status=self.status,
            comment=normalized_comment,
            now=timestamp,
        )

    def approve(
        self,
        *,
        actor: str,
        comment: str = "",
        now: datetime | None = None,
    ) -> "DocumentWorkflowEvent":
        self._require_status(DocumentStatus.IN_REVIEW, action="approve")
        timestamp = now or datetime.now(UTC)
        previous = self.status
        self.status = DocumentStatus.APPROVED
        self.updated_at = timestamp
        self.approved_at = timestamp
        return DocumentWorkflowEvent.create(
            version_id=self.id,
            actor=actor,
            action=WorkflowAction.APPROVED,
            previous_status=previous,
            new_status=self.status,
            comment=comment,
            now=timestamp,
        )

    def supersede(
        self,
        *,
        actor: str,
        comment: str = "",
        now: datetime | None = None,
    ) -> "DocumentWorkflowEvent":
        self._require_status(DocumentStatus.APPROVED, action="supersede")
        timestamp = now or datetime.now(UTC)
        previous = self.status
        self.status = DocumentStatus.SUPERSEDED
        self.updated_at = timestamp
        self.superseded_at = timestamp
        return DocumentWorkflowEvent.create(
            version_id=self.id,
            actor=actor,
            action=WorkflowAction.SUPERSEDED,
            previous_status=previous,
            new_status=self.status,
            comment=comment,
            now=timestamp,
        )

    def _require_status(self, expected: DocumentStatus, *, action: str) -> None:
        if self.status is not expected:
            raise InvalidDocumentWorkflowTransitionError(
                f"Cannot {action} document version {self.version_number} while status is "
                f"{self.status.value}."
            )


@dataclass(frozen=True, slots=True)
class DocumentWorkflowEvent:
    id: WorkflowEventId
    version_id: DocumentVersionId
    actor: str
    action: WorkflowAction
    previous_status: DocumentStatus | None
    new_status: DocumentStatus
    comment: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        version_id: DocumentVersionId,
        actor: str,
        action: WorkflowAction,
        previous_status: DocumentStatus | None,
        new_status: DocumentStatus,
        comment: str,
        now: datetime | None = None,
    ) -> "DocumentWorkflowEvent":
        return cls(
            id=WorkflowEventId.new(),
            version_id=version_id,
            actor=_actor(actor),
            action=action,
            previous_status=previous_status,
            new_status=new_status,
            comment=_comment(comment),
            created_at=now or datetime.now(UTC),
        )


def _actor(value: str) -> str:
    normalized = " ".join(value.split())
    if not 2 <= len(normalized) <= 80:
        raise InvalidDocumentActorError("Actor must contain 2-80 characters.")
    return normalized


def _comment(value: str, *, required: bool = False) -> str:
    normalized = value.strip()
    if required and not normalized:
        raise InvalidDocumentCommentError("A review comment is required for this action.")
    if len(normalized) > 1000:
        raise InvalidDocumentCommentError(
            "Document workflow comments must not exceed 1000 characters."
        )
    return normalized


def _revision_reason(value: str) -> str:
    normalized = value.strip()
    if len(normalized) > 500:
        raise InvalidDocumentRevisionReasonError(
            "Document revision reason must not exceed 500 characters."
        )
    return normalized
