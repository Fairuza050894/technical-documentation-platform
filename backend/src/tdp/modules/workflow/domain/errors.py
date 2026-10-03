class WorkflowError(Exception):
    code = "workflow_error"


class InvalidWorkflowItemIdError(WorkflowError):
    code = "invalid_workflow_item_id"


class InvalidWorkflowEntityError(WorkflowError):
    code = "invalid_workflow_entity"


class InvalidWorkflowTitleError(WorkflowError):
    code = "invalid_workflow_title"


class InvalidWorkflowPriorityError(WorkflowError):
    code = "invalid_workflow_priority"


class InvalidWorkflowTransitionError(WorkflowError):
    code = "invalid_workflow_transition"


class InvalidWorkflowAssigneeError(WorkflowError):
    code = "invalid_workflow_assignee"


class InvalidWorkflowCommentError(WorkflowError):
    code = "invalid_workflow_comment"


class WorkflowItemNotFoundError(WorkflowError):
    code = "workflow_item_not_found"


class WorkflowEntityNotFoundError(WorkflowError):
    code = "workflow_entity_not_found"


class WorkflowProjectNotFoundError(WorkflowError):
    code = "workflow_project_not_found"


class WorkflowWorkspaceMismatchError(WorkflowError):
    code = "workflow_workspace_mismatch"


class WorkflowProjectArchivedError(WorkflowError):
    code = "workflow_project_archived"
