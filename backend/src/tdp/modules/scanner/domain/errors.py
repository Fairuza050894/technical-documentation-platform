class ScannerError(Exception):
    code: str = "SCANNER_ERROR"


class RepositoryCloneError(ScannerError):
    code = "REPOSITORY_CLONE_ERROR"


class RepositoryNotFoundError(ScannerError):
    code = "REPOSITORY_NOT_FOUND"


class AnalysisError(ScannerError):
    code = "ANALYSIS_ERROR"


class ScanNotFoundError(ScannerError):
    code = "SCAN_NOT_FOUND"


class ScanInProgressError(ScannerError):
    code = "SCAN_IN_PROGRESS"
