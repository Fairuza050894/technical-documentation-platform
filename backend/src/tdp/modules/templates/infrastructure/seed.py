from tdp.modules.templates.infrastructure.builtin_templates import BUILTIN_TEMPLATES
from tdp.modules.templates.infrastructure.sqlite_repository import SqliteTemplateRepository


async def seed_builtin_templates(repository: SqliteTemplateRepository) -> int:
    inserted = 0
    for template in BUILTIN_TEMPLATES:
        existing = await repository.get_by_key(template.key)
        if existing is None:
            await repository.add(template)
            inserted += 1
    return inserted
