from typing import ClassVar


class CatalogError(Exception):
    """Base error for API catalog and synchronization failures."""

    code: ClassVar[str] = "CATALOG_ERROR"


class InvalidSynchronizationIdError(CatalogError):
    code = "INVALID_SYNCHRONIZATION_ID"


class CatalogSourceNotFoundError(CatalogError):
    code = "CATALOG_SOURCE_NOT_FOUND"


class CatalogSourceArchivedError(CatalogError):
    code = "CATALOG_SOURCE_ARCHIVED"


class CatalogProjectNotFoundError(CatalogError):
    code = "CATALOG_PROJECT_NOT_FOUND"


class CatalogProjectArchivedError(CatalogError):
    code = "CATALOG_PROJECT_ARCHIVED"


class CatalogArtifactNotFoundError(CatalogError):
    code = "CATALOG_ARTIFACT_NOT_FOUND"


class CatalogArtifactIntegrityError(CatalogError):
    code = "CATALOG_ARTIFACT_INTEGRITY_ERROR"


class InvalidCatalogDocumentError(CatalogError):
    code = "INVALID_CATALOG_DOCUMENT"


class SynchronizationNotFoundError(CatalogError):
    code = "SYNCHRONIZATION_NOT_FOUND"
