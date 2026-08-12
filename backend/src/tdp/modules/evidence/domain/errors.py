from typing import ClassVar


class EvidenceError(Exception):
    """Base error for evidence and claim failures."""

    code: ClassVar[str] = "EVIDENCE_ERROR"


class InvalidEvidenceArtifactIdError(EvidenceError):
    code = "INVALID_EVIDENCE_ARTIFACT_ID"


class InvalidEvidenceChecksumError(EvidenceError):
    code = "INVALID_EVIDENCE_CHECKSUM"


class InvalidEvidenceKindError(EvidenceError):
    code = "INVALID_EVIDENCE_KIND"


class InvalidEvidenceCaptureTimeError(EvidenceError):
    code = "INVALID_EVIDENCE_CAPTURE_TIME"


class InvalidEvidenceReferenceError(EvidenceError):
    code = "INVALID_EVIDENCE_REFERENCE"


class EvidenceArtifactNotFoundError(EvidenceError):
    code = "EVIDENCE_ARTIFACT_NOT_FOUND"


class EvidenceOriginConflictError(EvidenceError):
    code = "EVIDENCE_ORIGIN_CONFLICT"


class InvalidEvidenceManifestError(EvidenceError):
    code = "INVALID_EVIDENCE_MANIFEST"


class EvidenceMaterializationChecksumMismatchError(EvidenceError):
    code = "EVIDENCE_MATERIALIZATION_CHECKSUM_MISMATCH"


class EvidenceMaterializationConflictError(EvidenceError):
    code = "EVIDENCE_MATERIALIZATION_CONFLICT"


class EvidenceMaterializationNotFoundError(EvidenceError):
    code = "EVIDENCE_MATERIALIZATION_NOT_FOUND"


class EvidenceProjectNotFoundError(EvidenceError):
    code = "EVIDENCE_PROJECT_NOT_FOUND"


class EvidenceProjectArchivedError(EvidenceError):
    code = "EVIDENCE_PROJECT_ARCHIVED"


class EvidenceWorkspaceNotFoundError(EvidenceError):
    code = "EVIDENCE_WORKSPACE_NOT_FOUND"


class EvidenceWorkspaceArchivedError(EvidenceError):
    code = "EVIDENCE_WORKSPACE_ARCHIVED"


class EvidenceSourceNotFoundError(EvidenceError):
    code = "EVIDENCE_SOURCE_NOT_FOUND"


class EvidenceSnapshotNotFoundError(EvidenceError):
    code = "EVIDENCE_SNAPSHOT_NOT_FOUND"


class EvidenceSnapshotNotCompletedError(EvidenceError):
    code = "EVIDENCE_SNAPSHOT_NOT_COMPLETED"


class EvidenceFeatureNotFoundError(EvidenceError):
    code = "EVIDENCE_FEATURE_NOT_FOUND"


class EvidenceFeatureArchivedError(EvidenceError):
    code = "EVIDENCE_FEATURE_ARCHIVED"


class InvalidClaimIdError(EvidenceError):
    code = "INVALID_CLAIM_ID"


class InvalidClaimStatementError(EvidenceError):
    code = "INVALID_CLAIM_STATEMENT"


class InvalidClaimClassificationError(EvidenceError):
    code = "INVALID_CLAIM_CLASSIFICATION"


class InvalidClaimEvidenceError(EvidenceError):
    code = "INVALID_CLAIM_EVIDENCE"


class InvalidClaimDerivationError(EvidenceError):
    code = "INVALID_CLAIM_DERIVATION"


class InvalidClaimDocumentTypeError(EvidenceError):
    code = "INVALID_CLAIM_DOCUMENT_TYPE"


class ClaimNotFoundError(EvidenceError):
    code = "CLAIM_NOT_FOUND"
