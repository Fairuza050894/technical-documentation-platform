import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from tdp.modules.evidence.domain.errors import (
    EvidenceMaterializationChecksumMismatchError,
    InvalidEvidenceManifestError,
)
from tdp.modules.evidence.domain.model import (
    REFERENCED_EVIDENCE_KINDS,
    EvidenceArtifactId,
    EvidenceChecksum,
    EvidenceKind,
)

SEMANTIC_EVIDENCE_MANIFEST_SCHEMA_VERSION = "semantic-evidence-manifest-v1"

type NormalizedObject = dict[str, object]

_REFERENCE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:[^\s]+$")
_CONFIGURATION_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]{0,127}$")
_SECRET_PATTERN = re.compile(
    r"(?i)(?:"
    r"-----BEGIN [^-]*(?:PRIVATE KEY|OPENSSH PRIVATE KEY)-----"
    r"|(?:password|passwd|token|secret|api[_-]?key|authorization)"
    r"\s*[:=]\s*\S+"
    r"|bearer\s+[A-Za-z0-9._~+/=-]{8,}"
    r")"
)


@dataclass(frozen=True, slots=True)
class CanonicalSemanticEvidenceManifest:
    kind: EvidenceKind
    schema_version: str
    canonical_json: str
    checksum: EvidenceChecksum


@dataclass(frozen=True, slots=True)
class EvidenceMaterialization:
    evidence_id: EvidenceArtifactId
    project_id: str
    kind: EvidenceKind
    schema_version: str
    canonical_manifest: str
    checksum: EvidenceChecksum
    materialized_by: str
    materialized_at: datetime

    def __post_init__(self) -> None:
        calculated = hashlib.sha256(self.canonical_manifest.encode("utf-8")).hexdigest()
        if calculated != str(self.checksum):
            raise EvidenceMaterializationChecksumMismatchError(
                "Persisted materialized evidence does not match its checksum."
            )

    @classmethod
    def create(
        cls,
        *,
        evidence_id: EvidenceArtifactId,
        project_id: str,
        expected_checksum: EvidenceChecksum,
        manifest: CanonicalSemanticEvidenceManifest,
        materialized_by: str,
        materialized_at: datetime,
    ) -> "EvidenceMaterialization":
        if manifest.checksum != expected_checksum:
            raise EvidenceMaterializationChecksumMismatchError(
                "The typed semantic manifest checksum does not match the Evidence Artifact."
            )
        if materialized_at.tzinfo is None or materialized_at.utcoffset() is None:
            raise InvalidEvidenceManifestError(
                "Materialization time must include an explicit timezone."
            )
        return cls(
            evidence_id=evidence_id,
            project_id=_text(project_id, "Project reference", 100),
            kind=manifest.kind,
            schema_version=manifest.schema_version,
            canonical_manifest=manifest.canonical_json,
            checksum=manifest.checksum,
            materialized_by=_text(materialized_by, "Materializer identity", 300),
            materialized_at=materialized_at,
        )


def canonicalize_semantic_evidence_manifest(
    kind: EvidenceKind,
    manifest: Mapping[str, object],
) -> CanonicalSemanticEvidenceManifest:
    if kind not in REFERENCED_EVIDENCE_KINDS:
        raise InvalidEvidenceManifestError(
            "Only USER_JOURNEY, DEPLOYMENT_RUNTIME, and UAT_RESULT can be materialized."
        )

    _exact_keys(
        manifest,
        {"schema_version", "kind", "payload"},
        "Semantic evidence manifest",
    )
    schema_version = _text(manifest["schema_version"], "Manifest schema version", 100)
    if schema_version != SEMANTIC_EVIDENCE_MANIFEST_SCHEMA_VERSION:
        raise InvalidEvidenceManifestError(
            f"Manifest schema must be {SEMANTIC_EVIDENCE_MANIFEST_SCHEMA_VERSION}."
        )

    manifest_kind = _text(manifest["kind"], "Manifest evidence kind", 100).upper()
    if manifest_kind != kind.value:
        raise InvalidEvidenceManifestError(
            "Manifest evidence kind must match the referenced Evidence Artifact."
        )

    payload = _mapping(manifest["payload"], "Manifest payload")
    if kind is EvidenceKind.USER_JOURNEY:
        normalized_payload = _normalize_user_journey(payload)
    elif kind is EvidenceKind.DEPLOYMENT_RUNTIME:
        normalized_payload = _normalize_deployment_runtime(payload)
    else:
        normalized_payload = _normalize_uat_result(payload)

    normalized: NormalizedObject = {
        "schema_version": SEMANTIC_EVIDENCE_MANIFEST_SCHEMA_VERSION,
        "kind": kind.value,
        "payload": normalized_payload,
    }
    canonical_json = json.dumps(
        normalized,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    checksum = EvidenceChecksum(hashlib.sha256(canonical_json.encode("utf-8")).hexdigest())
    return CanonicalSemanticEvidenceManifest(
        kind=kind,
        schema_version=SEMANTIC_EVIDENCE_MANIFEST_SCHEMA_VERSION,
        canonical_json=canonical_json,
        checksum=checksum,
    )


def _normalize_user_journey(payload: Mapping[str, object]) -> NormalizedObject:
    _exact_keys(
        payload,
        {"journey_name", "actors", "preconditions", "steps", "outcomes"},
        "USER_JOURNEY payload",
    )
    steps = _mapping_list(payload["steps"], "Journey steps", maximum=100)
    normalized_steps = [
        _normalize_journey_step(item, index + 1) for index, item in enumerate(steps)
    ]
    _require_contiguous_sequence(normalized_steps, "Journey steps")
    return {
        "journey_name": _safe_text(payload["journey_name"], "Journey name", 300),
        "actors": sorted(set(_text_list(payload["actors"], "Journey actors", maximum=50))),
        "preconditions": _text_list(
            payload["preconditions"],
            "Journey preconditions",
            maximum=100,
        ),
        "steps": normalized_steps,
        "outcomes": _text_list(
            payload["outcomes"],
            "Journey outcomes",
            maximum=100,
        ),
    }


def _normalize_journey_step(
    item: Mapping[str, object],
    fallback_sequence: int,
) -> NormalizedObject:
    _exact_keys(
        item,
        {"sequence", "actor", "action", "expected_outcome", "source_reference"},
        "Journey step",
    )
    return {
        "sequence": _positive_int(
            item.get("sequence", fallback_sequence),
            "Journey sequence",
        ),
        "actor": _safe_text(item["actor"], "Journey actor", 200),
        "action": _safe_text(item["action"], "Journey action", 1000),
        "expected_outcome": _safe_text(
            item["expected_outcome"],
            "Journey expected outcome",
            1000,
        ),
        "source_reference": _reference(
            item["source_reference"],
            "Journey source reference",
        ),
    }


def _normalize_deployment_runtime(
    payload: Mapping[str, object],
) -> NormalizedObject:
    _exact_keys(
        payload,
        {
            "environment",
            "runtime_components",
            "prerequisites",
            "configuration_keys",
            "deployment_steps",
            "verification_checks",
            "rollback_references",
        },
        "DEPLOYMENT_RUNTIME payload",
    )
    components = _mapping_list(
        payload["runtime_components"],
        "Runtime components",
        maximum=100,
    )
    deployment_steps = _mapping_list(
        payload["deployment_steps"],
        "Deployment steps",
        maximum=100,
    )
    verification_checks = _mapping_list(
        payload["verification_checks"],
        "Verification checks",
        maximum=100,
    )
    normalized_steps = [
        _normalize_deployment_step(item, index + 1) for index, item in enumerate(deployment_steps)
    ]
    _require_contiguous_sequence(normalized_steps, "Deployment steps")

    configuration_keys = _text_list(
        payload["configuration_keys"],
        "Configuration keys",
        maximum=200,
    )
    for key in configuration_keys:
        if not _CONFIGURATION_NAME_PATTERN.fullmatch(key):
            raise InvalidEvidenceManifestError(
                "Configuration keys must contain names only, never values."
            )

    return {
        "environment": _safe_text(
            payload["environment"],
            "Deployment environment",
            200,
        ),
        "runtime_components": sorted(
            (_normalize_runtime_component(item) for item in components),
            key=lambda item: (str(item["name"]), str(item["version"])),
        ),
        "prerequisites": _text_list(
            payload["prerequisites"],
            "Deployment prerequisites",
            maximum=100,
        ),
        "configuration_keys": sorted(set(configuration_keys)),
        "deployment_steps": normalized_steps,
        "verification_checks": [
            _normalize_verification_check(item) for item in verification_checks
        ],
        "rollback_references": sorted(
            set(
                _reference(item, "Rollback reference")
                for item in _raw_list(
                    payload["rollback_references"],
                    "Rollback references",
                    maximum=100,
                )
            )
        ),
    }


def _normalize_runtime_component(
    item: Mapping[str, object],
) -> NormalizedObject:
    _exact_keys(
        item,
        {"name", "version", "source_reference"},
        "Runtime component",
    )
    return {
        "name": _safe_text(item["name"], "Runtime component name", 200),
        "version": _safe_text(item["version"], "Runtime component version", 100),
        "source_reference": _reference(
            item["source_reference"],
            "Runtime component source reference",
        ),
    }


def _normalize_deployment_step(
    item: Mapping[str, object],
    fallback_sequence: int,
) -> NormalizedObject:
    _exact_keys(
        item,
        {"sequence", "instruction", "source_reference"},
        "Deployment step",
    )
    return {
        "sequence": _positive_int(
            item.get("sequence", fallback_sequence),
            "Deployment sequence",
        ),
        "instruction": _safe_text(
            item["instruction"],
            "Deployment instruction",
            1500,
        ),
        "source_reference": _reference(
            item["source_reference"],
            "Deployment source reference",
        ),
    }


def _normalize_verification_check(
    item: Mapping[str, object],
) -> NormalizedObject:
    _exact_keys(
        item,
        {"name", "expected_result", "source_reference"},
        "Verification check",
    )
    return {
        "name": _safe_text(item["name"], "Verification name", 300),
        "expected_result": _safe_text(
            item["expected_result"],
            "Verification expected result",
            1000,
        ),
        "source_reference": _reference(
            item["source_reference"],
            "Verification source reference",
        ),
    }


def _normalize_uat_result(payload: Mapping[str, object]) -> NormalizedObject:
    _exact_keys(
        payload,
        {"run_reference", "executed_at", "scenarios"},
        "UAT_RESULT payload",
    )
    scenarios = _mapping_list(
        payload["scenarios"],
        "UAT scenarios",
        maximum=500,
    )
    normalized_scenarios = [_normalize_uat_scenario(item) for item in scenarios]
    identifiers = [str(item["scenario_id"]) for item in normalized_scenarios]
    if len(identifiers) != len(set(identifiers)):
        raise InvalidEvidenceManifestError("UAT scenario IDs must be unique.")

    return {
        "run_reference": _reference(
            payload["run_reference"],
            "UAT run reference",
        ),
        "executed_at": _aware_datetime_text(
            payload["executed_at"],
            "UAT execution time",
        ),
        "scenarios": sorted(
            normalized_scenarios,
            key=lambda item: str(item["scenario_id"]),
        ),
    }


def _normalize_uat_scenario(
    item: Mapping[str, object],
) -> NormalizedObject:
    _exact_keys(
        item,
        {
            "scenario_id",
            "title",
            "status",
            "expected_result",
            "actual_result",
            "evidence_references",
        },
        "UAT scenario",
    )
    status = _text(item["status"], "UAT status", 20).upper()
    if status not in {"PASSED", "FAILED", "BLOCKED"}:
        raise InvalidEvidenceManifestError(
            "UAT scenario status must be PASSED, FAILED, or BLOCKED."
        )
    return {
        "scenario_id": _safe_text(
            item["scenario_id"],
            "UAT scenario ID",
            200,
        ),
        "title": _safe_text(item["title"], "UAT scenario title", 500),
        "status": status,
        "expected_result": _safe_text(
            item["expected_result"],
            "UAT expected result",
            1000,
        ),
        "actual_result": _safe_text(
            item["actual_result"],
            "UAT actual result",
            1000,
        ),
        "evidence_references": sorted(
            set(
                _reference(value, "UAT evidence reference")
                for value in _raw_list(
                    item["evidence_references"],
                    "UAT evidence references",
                    maximum=100,
                )
            )
        ),
    }


def _exact_keys(
    value: Mapping[str, object],
    expected: set[str],
    label: str,
) -> None:
    actual = set(value)
    if actual == expected:
        return

    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    details: list[str] = []
    if missing:
        details.append("missing=" + ",".join(missing))
    if extra:
        details.append("extra=" + ",".join(extra))
    raise InvalidEvidenceManifestError(f"{label} has an invalid field set ({'; '.join(details)}).")


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise InvalidEvidenceManifestError(f"{label} must be an object.")
    return value


def _mapping_list(
    value: object,
    label: str,
    *,
    maximum: int,
) -> list[Mapping[str, object]]:
    return [_mapping(item, label) for item in _raw_list(value, label, maximum=maximum)]


def _raw_list(
    value: object,
    label: str,
    *,
    maximum: int,
) -> list[object]:
    if not isinstance(value, list) or not 1 <= len(value) <= maximum:
        raise InvalidEvidenceManifestError(f"{label} must contain between 1 and {maximum} items.")
    return value


def _text_list(
    value: object,
    label: str,
    *,
    maximum: int,
) -> list[str]:
    return [_safe_text(item, label, 1500) for item in _raw_list(value, label, maximum=maximum)]


def _text(value: object, label: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise InvalidEvidenceManifestError(f"{label} must be text.")
    normalized = " ".join(value.split())
    if not normalized or len(normalized) > maximum:
        raise InvalidEvidenceManifestError(f"{label} must contain 1-{maximum} characters.")
    return normalized


def _safe_text(value: object, label: str, maximum: int) -> str:
    normalized = _text(value, label, maximum)
    if _SECRET_PATTERN.search(normalized):
        raise InvalidEvidenceManifestError(
            f"{label} appears to contain secret material; use a governed reference instead."
        )
    return normalized


def _reference(value: object, label: str) -> str:
    normalized = _safe_text(value, label, 500)
    if not _REFERENCE_PATTERN.fullmatch(normalized):
        raise InvalidEvidenceManifestError(
            f"{label} must be an opaque reference with an explicit scheme."
        )
    if normalized.casefold().startswith(("file:", "http:", "https:")):
        raise InvalidEvidenceManifestError(
            f"{label} must not use file or direct HTTP(S) references."
        )
    return normalized


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise InvalidEvidenceManifestError(f"{label} must be a positive integer.")
    return value


def _require_contiguous_sequence(
    items: list[NormalizedObject],
    label: str,
) -> None:
    sequences: list[int] = []
    for item in items:
        sequence = item["sequence"]
        if isinstance(sequence, bool) or not isinstance(sequence, int):
            raise InvalidEvidenceManifestError(f"{label} sequence must contain integers.")
        sequences.append(sequence)

    if sequences != list(range(1, len(items) + 1)):
        raise InvalidEvidenceManifestError(f"{label} sequence must be contiguous and begin at 1.")


def _aware_datetime_text(value: object, label: str) -> str:
    normalized = _text(value, label, 100)
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidEvidenceManifestError(f"{label} must be an ISO-8601 timestamp.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InvalidEvidenceManifestError(f"{label} must include an explicit timezone.")
    return parsed.isoformat()
