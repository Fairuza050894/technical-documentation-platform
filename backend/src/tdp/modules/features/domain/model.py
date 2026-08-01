import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from tdp.modules.features.domain.errors import (
    FeatureAlreadyArchivedError,
    InvalidFeatureDescriptionError,
    InvalidFeatureIdError,
    InvalidFeatureKeyError,
    InvalidFeatureNameError,
    InvalidFeatureOwnerError,
    InvalidFeatureProjectIdError,
)

_FEATURE_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]{1,29}$")
FEATURE_DOCUMENTATION_POLICY_KEY = "feature-documentation-baseline-v1"


class FeatureKind(StrEnum):
    FEATURE = "FEATURE"
    MODULE = "MODULE"


class FeatureStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class DocumentationType(StrEnum):
    BUSINESS_REQUIREMENT = "BUSINESS_REQUIREMENT"
    SYSTEM_REQUIREMENTS_SPECIFICATION = "SYSTEM_REQUIREMENTS_SPECIFICATION"
    FUNCTIONAL_SPECIFICATION = "FUNCTIONAL_SPECIFICATION"
    API_DOCUMENTATION = "API_DOCUMENTATION"
    DATABASE_SPECIFICATION = "DATABASE_SPECIFICATION"
    USER_GUIDE = "USER_GUIDE"
    TEST_SCENARIO = "TEST_SCENARIO"
    RELEASE_NOTE = "RELEASE_NOTE"


class DocumentationRequirement(StrEnum):
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"


class DocumentationCoverageStatus(StrEnum):
    MISSING = "MISSING"
    PLANNED = "PLANNED"
    AVAILABLE = "AVAILABLE"


@dataclass(frozen=True, slots=True)
class FeatureId:
    value: UUID

    @classmethod
    def new(cls) -> "FeatureId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "FeatureId":
        try:
            return cls(UUID(value))
        except ValueError as exc:
            raise InvalidFeatureIdError("Feature ID must be a valid UUID.") from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class FeatureKey:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not _FEATURE_KEY_PATTERN.fullmatch(normalized):
            raise InvalidFeatureKeyError(
                "Feature key must contain 2-30 uppercase letters, numbers, or hyphens."
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class FeatureName:
    value: str

    def __post_init__(self) -> None:
        normalized = " ".join(self.value.split())
        if not 3 <= len(normalized) <= 100:
            raise InvalidFeatureNameError("Feature name must contain 3-100 characters.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class FeatureDescription:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if len(normalized) > 1000:
            raise InvalidFeatureDescriptionError(
                "Feature description must not exceed 1000 characters."
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class FeatureOwner:
    value: str

    def __post_init__(self) -> None:
        normalized = " ".join(self.value.split())
        if len(normalized) > 120:
            raise InvalidFeatureOwnerError("Feature owner must not exceed 120 characters.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(slots=True)
class Feature:
    id: FeatureId
    project_id: str
    key: FeatureKey
    name: FeatureName
    description: FeatureDescription
    kind: FeatureKind
    owner: FeatureOwner
    status: FeatureStatus
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        try:
            UUID(self.project_id)
        except ValueError as exc:
            raise InvalidFeatureProjectIdError(
                "Feature project reference must be a valid UUID."
            ) from exc

    @classmethod
    def create(
        cls,
        *,
        project_id: str,
        key: FeatureKey,
        name: FeatureName,
        description: FeatureDescription,
        kind: FeatureKind,
        owner: FeatureOwner,
        now: datetime | None = None,
    ) -> "Feature":
        timestamp = now or datetime.now(UTC)
        return cls(
            id=FeatureId.new(),
            project_id=project_id,
            key=key,
            name=name,
            description=description,
            kind=kind,
            owner=owner,
            status=FeatureStatus.ACTIVE,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def archive(self, *, now: datetime | None = None) -> None:
        if self.status is FeatureStatus.ARCHIVED:
            raise FeatureAlreadyArchivedError(f"Feature {self.id} is already archived.")
        self.status = FeatureStatus.ARCHIVED
        self.updated_at = now or datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class FeatureDocumentationMapItem:
    feature_id: FeatureId
    document_type: DocumentationType
    requirement: DocumentationRequirement
    document_id: str | None
    policy_key: str
    created_at: datetime
    updated_at: datetime

    @property
    def coverage_status(self) -> DocumentationCoverageStatus:
        if self.document_id is not None:
            return DocumentationCoverageStatus.AVAILABLE
        if self.requirement is DocumentationRequirement.REQUIRED:
            return DocumentationCoverageStatus.MISSING
        return DocumentationCoverageStatus.PLANNED


def create_documentation_map(
    feature: Feature,
    *,
    now: datetime | None = None,
) -> list[FeatureDocumentationMapItem]:
    timestamp = now or feature.created_at
    requirements = _requirements_for_kind(feature.kind)
    return [
        FeatureDocumentationMapItem(
            feature_id=feature.id,
            document_type=document_type,
            requirement=requirement,
            document_id=None,
            policy_key=FEATURE_DOCUMENTATION_POLICY_KEY,
            created_at=timestamp,
            updated_at=timestamp,
        )
        for document_type, requirement in requirements
    ]


def _requirements_for_kind(
    kind: FeatureKind,
) -> tuple[tuple[DocumentationType, DocumentationRequirement], ...]:
    required_for_feature = {
        DocumentationType.BUSINESS_REQUIREMENT,
        DocumentationType.FUNCTIONAL_SPECIFICATION,
        DocumentationType.USER_GUIDE,
        DocumentationType.TEST_SCENARIO,
    }
    required_for_module = {
        DocumentationType.SYSTEM_REQUIREMENTS_SPECIFICATION,
        DocumentationType.FUNCTIONAL_SPECIFICATION,
        DocumentationType.API_DOCUMENTATION,
        DocumentationType.DATABASE_SPECIFICATION,
        DocumentationType.TEST_SCENARIO,
    }
    required = required_for_feature if kind is FeatureKind.FEATURE else required_for_module
    return tuple(
        (
            document_type,
            DocumentationRequirement.REQUIRED
            if document_type in required
            else DocumentationRequirement.OPTIONAL,
        )
        for document_type in DocumentationType
    )
