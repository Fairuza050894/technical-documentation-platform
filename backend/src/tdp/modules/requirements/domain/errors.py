from typing import ClassVar


class RequirementError(Exception):
    """Base error for requirement and traceability failures."""

    code: ClassVar[str] = "REQUIREMENT_ERROR"


class InvalidRequirementIdError(RequirementError):
    code = "INVALID_REQUIREMENT_ID"


class InvalidRequirementRevisionIdError(RequirementError):
    code = "INVALID_REQUIREMENT_REVISION_ID"


class InvalidRequirementKeyError(RequirementError):
    code = "INVALID_REQUIREMENT_KEY"


class InvalidRequirementTitleError(RequirementError):
    code = "INVALID_REQUIREMENT_TITLE"


class InvalidRequirementStatementError(RequirementError):
    code = "INVALID_REQUIREMENT_STATEMENT"


class InvalidRequirementOwnerError(RequirementError):
    code = "INVALID_REQUIREMENT_OWNER"


class InvalidRequirementActorError(RequirementError):
    code = "INVALID_REQUIREMENT_ACTOR"


class InvalidAcceptanceCriterionError(RequirementError):
    code = "INVALID_ACCEPTANCE_CRITERION"


class InvalidRequirementTypeError(RequirementError):
    code = "INVALID_REQUIREMENT_TYPE"


class RequirementKeyAlreadyExistsError(RequirementError):
    code = "REQUIREMENT_KEY_ALREADY_EXISTS"


class RequirementNotFoundError(RequirementError):
    code = "REQUIREMENT_NOT_FOUND"


class RequirementRetiredError(RequirementError):
    code = "REQUIREMENT_RETIRED"


class RequirementProjectNotFoundError(RequirementError):
    code = "REQUIREMENT_PROJECT_NOT_FOUND"


class RequirementWorkspaceMismatchError(RequirementError):
    code = "REQUIREMENT_WORKSPACE_MISMATCH"


class RequirementProjectArchivedError(RequirementError):
    code = "REQUIREMENT_PROJECT_ARCHIVED"


class InvalidTraceTargetError(RequirementError):
    code = "INVALID_TRACE_TARGET"


class InvalidTraceRelationError(RequirementError):
    code = "INVALID_TRACE_RELATION"


class TraceTargetNotFoundError(RequirementError):
    code = "TRACE_TARGET_NOT_FOUND"


class TraceLinkAlreadyExistsError(RequirementError):
    code = "TRACE_LINK_ALREADY_EXISTS"
