from typing import ClassVar


class FeatureError(Exception):
    """Base error for feature and module failures."""

    code: ClassVar[str] = "FEATURE_ERROR"


class InvalidFeatureIdError(FeatureError):
    code = "INVALID_FEATURE_ID"


class InvalidFeatureKeyError(FeatureError):
    code = "INVALID_FEATURE_KEY"


class InvalidFeatureNameError(FeatureError):
    code = "INVALID_FEATURE_NAME"


class InvalidFeatureDescriptionError(FeatureError):
    code = "INVALID_FEATURE_DESCRIPTION"


class InvalidFeatureOwnerError(FeatureError):
    code = "INVALID_FEATURE_OWNER"


class InvalidFeatureProjectIdError(FeatureError):
    code = "INVALID_FEATURE_PROJECT_ID"


class InvalidFeatureKindError(FeatureError):
    code = "INVALID_FEATURE_KIND"


class FeatureKeyAlreadyExistsError(FeatureError):
    code = "FEATURE_KEY_ALREADY_EXISTS"


class FeatureNotFoundError(FeatureError):
    code = "FEATURE_NOT_FOUND"


class FeatureProjectNotFoundError(FeatureError):
    code = "FEATURE_PROJECT_NOT_FOUND"


class FeatureWorkspaceMismatchError(FeatureError):
    code = "FEATURE_WORKSPACE_MISMATCH"


class FeatureProjectArchivedError(FeatureError):
    code = "FEATURE_PROJECT_ARCHIVED"


class FeatureAlreadyArchivedError(FeatureError):
    code = "FEATURE_ALREADY_ARCHIVED"
