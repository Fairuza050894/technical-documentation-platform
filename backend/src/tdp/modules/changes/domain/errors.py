from typing import ClassVar


class ChangeDetectionError(Exception):
    code: ClassVar[str] = "CHANGE_DETECTION_ERROR"


class InvalidComparisonError(ChangeDetectionError):
    code = "INVALID_COMPARISON"


class ComparisonRunNotFoundError(ChangeDetectionError):
    code = "COMPARISON_RUN_NOT_FOUND"
