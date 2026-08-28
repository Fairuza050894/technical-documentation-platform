class TemplateError(Exception):
    code: str = "TEMPLATE_ERROR"


class TemplateNotFoundError(TemplateError):
    code = "TEMPLATE_NOT_FOUND"


class TemplateKeyConflictError(TemplateError):
    code = "TEMPLATE_KEY_CONFLICT"


class TemplateBuiltinModificationError(TemplateError):
    code = "TEMPLATE_BUILTIN_MODIFICATION"


class TemplateValidationError(TemplateError):
    code = "TEMPLATE_VALIDATION_ERROR"
