from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GenerateTechnicalSourceOverviewCommand:
    project_id: str
    target_run_id: str
    baseline_run_id: str | None = None
    revision_reason: str = ""
    actor: str = "System Generator"


@dataclass(frozen=True, slots=True)
class DocumentWorkflowCommand:
    version_id: str
    actor: str
    comment: str = ""


@dataclass(frozen=True, slots=True)
class CompareDocumentVersionsCommand:
    baseline_version_id: str
    target_version_id: str
