from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class TemplateCategory(StrEnum):
    REQUIREMENTS = "REQUIREMENTS"
    ARCHITECTURE = "ARCHITECTURE"
    TESTING = "TESTING"
    OPERATIONS = "OPERATIONS"
    USER_FACING = "USER_FACING"
    GOVERNANCE = "GOVERNANCE"


class TemplateStandard(StrEnum):
    IEEE_830 = "IEEE 830"
    IEEE_829 = "IEEE 829"
    ISO_9001 = "ISO 9001:2015"
    ISO_27001 = "ISO 27001:2022"
    ISO_42010 = "ISO/IEC/IEEE 42010"
    ISO_26514 = "ISO/IEC 26514"
    BABOK = "BABOK"
    OPENAPI_3 = "OpenAPI 3.0"
    CUSTOM = "Custom"


@dataclass(frozen=True, slots=True)
class TemplateId:
    value: UUID

    @classmethod
    def new(cls) -> "TemplateId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "TemplateId":
        return cls(UUID(value))

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class DocumentTemplate:
    id: TemplateId
    key: str
    name: str
    description: str
    category: TemplateCategory
    standard: TemplateStandard
    content: str
    document_type: str | None
    is_builtin: bool
    version: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        key: str,
        name: str,
        description: str,
        category: TemplateCategory,
        standard: TemplateStandard,
        content: str,
        document_type: str | None = None,
        is_builtin: bool = False,
        now: datetime | None = None,
    ) -> "DocumentTemplate":
        timestamp = now or datetime.now(UTC)
        return cls(
            id=TemplateId.new(),
            key=key.strip().upper(),
            name=name.strip(),
            description=description.strip(),
            category=category,
            standard=standard,
            content=content,
            document_type=document_type,
            is_builtin=is_builtin,
            version=1,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def update_content(self, content: str, now: datetime | None = None) -> None:
        self.content = content
        self.version += 1
        self.updated_at = now or datetime.now(UTC)

    def update_metadata(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        now: datetime | None = None,
    ) -> None:
        if name is not None:
            self.name = name.strip()
        if description is not None:
            self.description = description.strip()
        self.updated_at = now or datetime.now(UTC)
