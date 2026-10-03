class GovernanceError(Exception):
    code = "GOVERNANCE_ERROR"


class InvalidRequirementError(GovernanceError):
    code = "INVALID_REQUIREMENT"


class RequirementNotFoundError(GovernanceError):
    code = "REQUIREMENT_NOT_FOUND"


class RequirementKeyAlreadyExistsError(GovernanceError):
    code = "REQUIREMENT_KEY_ALREADY_EXISTS"


class InvalidTraceLinkError(GovernanceError):
    code = "INVALID_TRACE_LINK"


class ImpactAssessmentNotFoundError(GovernanceError):
    code = "IMPACT_ASSESSMENT_NOT_FOUND"


class InvalidWorkflowTransitionError(GovernanceError):
    code = "INVALID_WORKFLOW_TRANSITION"
