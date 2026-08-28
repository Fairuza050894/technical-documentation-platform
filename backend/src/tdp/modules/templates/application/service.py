from tdp.modules.templates.application.dto import TemplateDto, TemplateSummaryDto
from tdp.modules.templates.domain.errors import (
    TemplateBuiltinModificationError,
    TemplateKeyConflictError,
    TemplateNotFoundError,
    TemplateValidationError,
)
from tdp.modules.templates.domain.model import (
    DocumentTemplate,
    TemplateCategory,
    TemplateId,
    TemplateStandard,
)
from tdp.modules.templates.domain.repository import TemplateRepository


class TemplateApplicationService:
    def __init__(self, repository: TemplateRepository) -> None:
        self._repository = repository

    async def get_template(self, template_id: str) -> TemplateDto:
        template = await self._repository.get(TemplateId.from_string(template_id))
        if template is None:
            raise TemplateNotFoundError(f"Template {template_id} was not found.")
        return TemplateDto.from_domain(template)

    async def get_template_by_key(self, key: str) -> TemplateDto:
        template = await self._repository.get_by_key(key.strip().upper())
        if template is None:
            raise TemplateNotFoundError(f"Template with key '{key}' was not found.")
        return TemplateDto.from_domain(template)

    async def list_templates(
        self,
        category: str | None = None,
        document_type: str | None = None,
    ) -> list[TemplateSummaryDto]:
        if category is not None:
            try:
                cat = TemplateCategory(category.strip().upper())
            except ValueError as exc:
                raise TemplateValidationError(
                    f"'{category}' is not a valid template category."
                ) from exc
            templates = await self._repository.list_by_category(cat)
        else:
            templates = await self._repository.list_all()

        if document_type is not None:
            normalized = document_type.strip().upper()
            templates = [
                t for t in templates
                if t.document_type is not None and t.document_type.upper() == normalized
            ]

        return [TemplateSummaryDto.from_domain(t) for t in templates]

    async def create_template(
        self,
        *,
        key: str,
        name: str,
        description: str,
        category: str,
        standard: str,
        content: str,
    ) -> TemplateDto:
        normalized_key = key.strip().upper()
        existing = await self._repository.get_by_key(normalized_key)
        if existing is not None:
            raise TemplateKeyConflictError(
                f"Template with key '{normalized_key}' already exists."
            )
        try:
            cat = TemplateCategory(category.strip().upper())
        except ValueError as exc:
            raise TemplateValidationError(
                f"'{category}' is not a valid template category."
            ) from exc
        try:
            std = TemplateStandard(standard.strip())
        except ValueError as exc:
            raise TemplateValidationError(
                f"'{standard}' is not a valid template standard."
            ) from exc
        if len(content.strip()) < 10:
            raise TemplateValidationError("Template content must be at least 10 characters.")
        template = DocumentTemplate.create(
            key=normalized_key,
            name=name,
            description=description,
            category=cat,
            standard=std,
            content=content,
        )
        await self._repository.add(template)
        return TemplateDto.from_domain(template)

    async def update_template(
        self,
        template_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        content: str | None = None,
    ) -> TemplateDto:
        template = await self._repository.get(TemplateId.from_string(template_id))
        if template is None:
            raise TemplateNotFoundError(f"Template {template_id} was not found.")
        if template.is_builtin:
            raise TemplateBuiltinModificationError(
                "Built-in templates cannot be modified. Create a custom copy instead."
            )
        if content is not None:
            if len(content.strip()) < 10:
                raise TemplateValidationError("Template content must be at least 10 characters.")
            template.update_content(content)
        if name is not None or description is not None:
            template.update_metadata(name=name, description=description)
        await self._repository.update(template)
        return TemplateDto.from_domain(template)

    async def delete_template(self, template_id: str) -> None:
        template = await self._repository.get(TemplateId.from_string(template_id))
        if template is None:
            raise TemplateNotFoundError(f"Template {template_id} was not found.")
        if template.is_builtin:
            raise TemplateBuiltinModificationError("Built-in templates cannot be deleted.")
        await self._repository.delete(template.id)

    async def duplicate_template(self, template_id: str, new_key: str) -> TemplateDto:
        source = await self._repository.get(TemplateId.from_string(template_id))
        if source is None:
            raise TemplateNotFoundError(f"Template {template_id} was not found.")
        normalized_key = new_key.strip().upper()
        existing = await self._repository.get_by_key(normalized_key)
        if existing is not None:
            raise TemplateKeyConflictError(
                f"Template with key '{normalized_key}' already exists."
            )
        copy = DocumentTemplate.create(
            key=normalized_key,
            name=f"{source.name} (Copy)",
            description=source.description,
            category=source.category,
            standard=source.standard,
            content=source.content,
            document_type=source.document_type,
        )
        await self._repository.add(copy)
        return TemplateDto.from_domain(copy)
