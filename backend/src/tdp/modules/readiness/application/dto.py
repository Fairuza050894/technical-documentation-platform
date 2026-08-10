from dataclasses import dataclass

from tdp.modules.readiness.domain.model import DocumentReadinessAssessment
from tdp.modules.readiness.domain.policy import READINESS_POLICY_VERSION


@dataclass(frozen=True, slots=True)
class ReadinessFindingDto:
    rule_code: str
    document_type: str
    severity: str
    message: str
    missing_input: str
    remediation: str
    supporting_references: list[str]


@dataclass(frozen=True, slots=True)
class DocumentReadinessDto:
    project_id: str
    policy_version: str
    document_type: str
    display_name: str
    automation_profile: str
    requirement: str
    availability: str
    latest_status: str | None
    readiness_state: str
    eligible: bool
    findings: list[ReadinessFindingDto]
    evidence_count: int
    observed_claim_count: int
    inferred_claim_count: int
    unverified_claim_count: int

    @classmethod
    def from_assessment(
        cls,
        *,
        project_id: str,
        display_name: str,
        automation_profile: str,
        requirement: str,
        availability: str,
        latest_status: str | None,
        assessment: DocumentReadinessAssessment,
    ) -> "DocumentReadinessDto":
        return cls(
            project_id=project_id,
            policy_version=READINESS_POLICY_VERSION,
            document_type=assessment.document_type,
            display_name=display_name,
            automation_profile=automation_profile,
            requirement=requirement,
            availability=availability,
            latest_status=latest_status,
            readiness_state=assessment.state.value,
            eligible=assessment.eligible,
            findings=[
                ReadinessFindingDto(
                    rule_code=item.rule_code,
                    document_type=item.document_type,
                    severity=item.severity.value,
                    message=item.message,
                    missing_input=item.missing_input,
                    remediation=item.remediation,
                    supporting_references=list(item.supporting_references),
                )
                for item in assessment.findings
            ],
            evidence_count=assessment.evidence_count,
            observed_claim_count=assessment.observed_claim_count,
            inferred_claim_count=assessment.inferred_claim_count,
            unverified_claim_count=assessment.unverified_claim_count,
        )


@dataclass(frozen=True, slots=True)
class ProjectReadinessDto:
    project_id: str
    project_status: str
    policy_version: str
    items: list[DocumentReadinessDto]
    total: int
    ready_total: int
    partially_ready_total: int
    not_ready_total: int
    eligible_total: int
    required_total: int
    required_not_ready_total: int

    @classmethod
    def create(
        cls,
        *,
        project_id: str,
        project_status: str,
        items: list[DocumentReadinessDto],
    ) -> "ProjectReadinessDto":
        return cls(
            project_id=project_id,
            project_status=project_status,
            policy_version=READINESS_POLICY_VERSION,
            items=items,
            total=len(items),
            ready_total=sum(item.readiness_state == "READY" for item in items),
            partially_ready_total=sum(item.readiness_state == "PARTIALLY_READY" for item in items),
            not_ready_total=sum(item.readiness_state == "NOT_READY" for item in items),
            eligible_total=sum(item.eligible for item in items),
            required_total=sum(item.requirement == "REQUIRED" for item in items),
            required_not_ready_total=sum(
                item.requirement == "REQUIRED" and item.readiness_state == "NOT_READY"
                for item in items
            ),
        )
