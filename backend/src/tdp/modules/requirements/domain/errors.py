class RequirementError(Exception):
    code = "requirement_error"


class InvalidRequirementIdError(RequirementError):
    code = "invalid_requirement_id"


class InvalidRequirementKeyError(RequirementError):
    code = "invalid_requirement_key"


class InvalidRequirementTitleError(RequirementError):
    code = "invalid_requirement_title"


class InvalidRequirementStatementError(RequirementError):
    code = "invalid_requirement_statement"


class InvalidRequirementAcceptanceCriteriaError(RequirementError):
    code = "invalid_requirement_acceptance_criteria"


class InvalidRequirementRationaleError(RequirementError):
    code = "invalid_requirement_rationale"


class InvalidRequirementTypeError(RequirementError):
    code = "invalid_requirement_type"


class InvalidRequirementStatusTransitionError(RequirementError):
    code = "invalid_requirement_status_transition"


class RequirementNotFoundError(RequirementError):
    code = "requirement_not_found"


class RequirementKeyAlreadyExistsError(RequirementError):
    code = "requirement_key_already_exists"


class RequirementProjectNotFoundError(RequirementError):
    code = "requirement_project_not_found"


class RequirementWorkspaceMismatchError(RequirementError):
    code = "requirement_workspace_mismatch"


class RequirementProjectArchivedError(RequirementError):
    code = "requirement_project_archived"


class RequirementFeatureNotFoundError(RequirementError):
    code = "requirement_feature_not_found"


class InvalidTraceabilityTargetError(RequirementError):
    code = "invalid_traceability_target"


class TraceabilityTargetNotFoundError(RequirementError):
    code = "traceability_target_not_found"


class TraceabilityLinkAlreadyExistsError(RequirementError):
    code = "traceability_link_already_exists"
