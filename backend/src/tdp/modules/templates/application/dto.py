from dataclasses import dataclass

from tdp.modules.templates.domain.model import DocumentTemplate


@dataclass(frozen=True, slots=True)
class TemplateDto:
    id: str
    key: str
    name: str
    description: str
    category: str
    standard: str
    content: str
    is_builtin: bool
    version: int
    created_at: str
    updated_at: str

    @classmethod
    def from_domain(cls, template: DocumentTemplate) -> "TemplateDto":
        return cls(
            id=str(template.id),
            key=template.key,
            name=template.name,
            description=template.description,
            category=template.category.value,
            standard=template.standard.value,
            content=template.content,
            is_builtin=template.is_builtin,
            version=template.version,
            created_at=template.created_at.isoformat(),
            updated_at=template.updated_at.isoformat(),
        )


@dataclass(frozen=True, slots=True)
class TemplateSummaryDto:
    id: str
    key: str
    name: str
    description: str
    category: str
    standard: str
    is_builtin: bool
    version: int
    section_count: int
    created_at: str
    updated_at: str

    @classmethod
    def from_domain(cls, template: DocumentTemplate) -> "TemplateSummaryDto":
        return cls(
            id=str(template.id),
            key=template.key,
            name=template.name,
            description=template.description,
            category=template.category.value,
            standard=template.standard.value,
            is_builtin=template.is_builtin,
            version=template.version,
            section_count=template.content.count("\n## "),
            created_at=template.created_at.isoformat(),
            updated_at=template.updated_at.isoformat(),
        )
