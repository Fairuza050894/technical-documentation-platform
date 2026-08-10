from dataclasses import dataclass
from enum import StrEnum


class ReadinessState(StrEnum):
    NOT_READY = "NOT_READY"
    PARTIALLY_READY = "PARTIALLY_READY"
    READY = "READY"


class ReadinessFindingSeverity(StrEnum):
    BLOCKER = "BLOCKER"
    WARNING = "WARNING"
    ADVISORY = "ADVISORY"


class ReadinessRuleKind(StrEnum):
    ANY_EVIDENCE = "ANY_EVIDENCE"
    EVIDENCE_KIND = "EVIDENCE_KIND"
    RELEVANT_CLAIM = "RELEVANT_CLAIM"
    APPROVED_DOCUMENTS = "APPROVED_DOCUMENTS"


@dataclass(frozen=True, slots=True)
class ReadinessEvidenceFact:
    reference: str
    kind: str


@dataclass(frozen=True, slots=True)
class ReadinessClaimFact:
    reference: str
    classification: str
    relevant_document_types: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReadinessDocumentFact:
    reference: str
    document_type: str
    status: str


@dataclass(frozen=True, slots=True)
class ReadinessRule:
    code: str
    kind: ReadinessRuleKind
    severity: ReadinessFindingSeverity
    message: str
    missing_input: str
    remediation: str
    evidence_kind: str = ""
    allowed_claim_classifications: tuple[str, ...] = ()
    required_document_types: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DocumentReadinessProfile:
    document_type: str
    rules: tuple[ReadinessRule, ...]


@dataclass(frozen=True, slots=True)
class ReadinessFinding:
    rule_code: str
    document_type: str
    severity: ReadinessFindingSeverity
    message: str
    missing_input: str
    remediation: str
    supporting_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DocumentReadinessAssessment:
    document_type: str
    state: ReadinessState
    eligible: bool
    findings: tuple[ReadinessFinding, ...]
    evidence_count: int
    observed_claim_count: int
    inferred_claim_count: int
    unverified_claim_count: int


class DeterministicReadinessEvaluator:
    def evaluate(
        self,
        *,
        profile: DocumentReadinessProfile,
        evidence: tuple[ReadinessEvidenceFact, ...],
        claims: tuple[ReadinessClaimFact, ...],
        documents: tuple[ReadinessDocumentFact, ...],
    ) -> DocumentReadinessAssessment:
        findings = tuple(
            finding
            for rule in profile.rules
            if (
                finding := self._evaluate_rule(
                    profile.document_type,
                    rule,
                    evidence,
                    claims,
                    documents,
                )
            )
            is not None
        )
        has_blocker = any(item.severity is ReadinessFindingSeverity.BLOCKER for item in findings)
        has_warning = any(item.severity is ReadinessFindingSeverity.WARNING for item in findings)
        state = (
            ReadinessState.NOT_READY
            if has_blocker
            else ReadinessState.PARTIALLY_READY
            if has_warning
            else ReadinessState.READY
        )
        relevant_claims = tuple(
            claim for claim in claims if profile.document_type in claim.relevant_document_types
        )
        return DocumentReadinessAssessment(
            document_type=profile.document_type,
            state=state,
            eligible=not has_blocker,
            findings=findings,
            evidence_count=len(evidence),
            observed_claim_count=_claim_count(relevant_claims, "OBSERVED"),
            inferred_claim_count=_claim_count(relevant_claims, "INFERRED"),
            unverified_claim_count=_claim_count(relevant_claims, "UNVERIFIED"),
        )

    @staticmethod
    def _evaluate_rule(
        document_type: str,
        rule: ReadinessRule,
        evidence: tuple[ReadinessEvidenceFact, ...],
        claims: tuple[ReadinessClaimFact, ...],
        documents: tuple[ReadinessDocumentFact, ...],
    ) -> ReadinessFinding | None:
        if rule.kind is ReadinessRuleKind.ANY_EVIDENCE:
            if evidence:
                return None
            return _finding(document_type, rule)

        if rule.kind is ReadinessRuleKind.EVIDENCE_KIND:
            matching = tuple(item for item in evidence if item.kind == rule.evidence_kind)
            if matching:
                return None
            return _finding(document_type, rule)

        if rule.kind is ReadinessRuleKind.RELEVANT_CLAIM:
            relevant = tuple(
                claim for claim in claims if document_type in claim.relevant_document_types
            )
            accepted = tuple(
                claim
                for claim in relevant
                if claim.classification in rule.allowed_claim_classifications
            )
            if accepted:
                return None
            return _finding(
                document_type,
                rule,
                tuple(f"{claim.reference}:{claim.classification}" for claim in relevant),
            )

        if rule.kind is ReadinessRuleKind.APPROVED_DOCUMENTS:
            by_type = {item.document_type: item for item in documents}
            unmet = tuple(
                required
                for required in rule.required_document_types
                if required not in by_type or by_type[required].status != "APPROVED"
            )
            if not unmet:
                return None
            references = tuple(
                (
                    f"document:{required}:MISSING"
                    if required not in by_type
                    else f"{by_type[required].reference}:{by_type[required].status}"
                )
                for required in unmet
            )
            return _finding(
                document_type,
                rule,
                references,
                missing_input="approved-documents:" + ",".join(unmet),
            )

        raise ValueError(f"Unsupported readiness rule kind: {rule.kind}")


def _finding(
    document_type: str,
    rule: ReadinessRule,
    references: tuple[str, ...] = (),
    *,
    missing_input: str | None = None,
) -> ReadinessFinding:
    return ReadinessFinding(
        rule_code=rule.code,
        document_type=document_type,
        severity=rule.severity,
        message=rule.message,
        missing_input=missing_input or rule.missing_input,
        remediation=rule.remediation,
        supporting_references=references,
    )


def _claim_count(
    claims: tuple[ReadinessClaimFact, ...],
    classification: str,
) -> int:
    return sum(item.classification == classification for item in claims)
