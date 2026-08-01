from dataclasses import dataclass

from tdp.identity.model import RequestPrincipal


@dataclass(frozen=True, slots=True)
class GenerateTechnicalSourceOverviewCommand:
    project_id: str
    target_run_id: str
    principal: RequestPrincipal
    baseline_run_id: str | None = None
    revision_reason: str = ""


@dataclass(frozen=True, slots=True)
class DocumentWorkflowCommand:
    version_id: str
    principal: RequestPrincipal
    comment: str = ""


@dataclass(frozen=True, slots=True)
class CompareDocumentVersionsCommand:
    baseline_version_id: str
    target_version_id: str
