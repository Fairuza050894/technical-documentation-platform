from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateRequirementCommand:
    workspace_id: str
    project_id: str
    key: str
    requirement_type: str
    title: str
    statement: str
    owner: str
    feature_id: str | None
    acceptance_criteria: tuple[str, ...]
    actor: str
    change_reason: str


@dataclass(frozen=True, slots=True)
class ReviseRequirementCommand:
    workspace_id: str
    project_id: str
    requirement_id: str
    requirement_type: str
    title: str
    statement: str
    owner: str
    feature_id: str | None
    acceptance_criteria: tuple[str, ...]
    actor: str
    change_reason: str


@dataclass(frozen=True, slots=True)
class RetireRequirementCommand:
    workspace_id: str
    project_id: str
    requirement_id: str
    actor: str
    change_reason: str


@dataclass(frozen=True, slots=True)
class CreateTraceLinkCommand:
    workspace_id: str
    project_id: str
    requirement_id: str
    target_type: str
    relation: str
    target_reference: str
    actor: str
