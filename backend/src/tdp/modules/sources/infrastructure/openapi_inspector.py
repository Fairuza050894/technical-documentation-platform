import hashlib
import json
from collections.abc import Mapping
from typing import Any, cast

import yaml

from tdp.modules.sources.application.ports import OpenApiInspection
from tdp.modules.sources.domain.errors import (
    InvalidOpenApiDocumentError,
    UnsupportedOpenApiVersionError,
    UnsupportedSourceFileError,
)
from tdp.modules.sources.domain.model import SourceFileName, SourceMediaType

_HTTP_METHODS = {
    "get",
    "put",
    "post",
    "delete",
    "options",
    "head",
    "patch",
    "trace",
}


class DeterministicOpenApiInspector:
    def inspect(self, file_name: SourceFileName, content: bytes) -> OpenApiInspection:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InvalidOpenApiDocumentError(
                "OpenAPI source file must use UTF-8 encoding."
            ) from exc

        document, media_type = self._load_document(file_name, text)
        root = self._require_mapping(document, "OpenAPI document root")
        if "openapi" not in root and "swagger" in root:
            raise UnsupportedOpenApiVersionError(
                "Swagger 2.0 is not supported; provide OpenAPI 3.0.x or 3.1.x."
            )
        openapi_version = self._require_text(root, "openapi")
        if not openapi_version.startswith(("3.0.", "3.1.")):
            raise UnsupportedOpenApiVersionError(
                "MVP 1 supports OpenAPI 3.0.x and 3.1.x specifications."
            )

        info = self._require_mapping(root.get("info"), "info")
        api_title = self._require_text(info, "title")
        api_version = self._require_text(info, "version")
        paths = self._require_mapping(root.get("paths"), "paths")
        operation_count = sum(
            1
            for path_item in paths.values()
            if isinstance(path_item, Mapping)
            for key in path_item
            if isinstance(key, str) and key.lower() in _HTTP_METHODS
        )

        return OpenApiInspection(
            media_type=media_type,
            checksum=hashlib.sha256(content).hexdigest(),
            openapi_version=openapi_version,
            api_title=api_title,
            api_version=api_version,
            path_count=len(paths),
            operation_count=operation_count,
        )

    @staticmethod
    def _load_document(file_name: SourceFileName, text: str) -> tuple[Any, SourceMediaType]:
        try:
            if file_name.suffix == ".json":
                return json.loads(text), SourceMediaType.JSON
            if file_name.suffix in {".yaml", ".yml"}:
                return yaml.safe_load(text), SourceMediaType.YAML
        except (json.JSONDecodeError, yaml.YAMLError) as exc:
            raise InvalidOpenApiDocumentError(
                "OpenAPI source file contains invalid JSON or YAML syntax."
            ) from exc
        raise UnsupportedSourceFileError("OpenAPI source file type is not supported.")

    @staticmethod
    def _require_mapping(value: object, label: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise InvalidOpenApiDocumentError(f"{label} must be an object.")
        return cast(Mapping[str, Any], value)

    @staticmethod
    def _require_text(mapping: Mapping[str, Any], key: str) -> str:
        value = mapping.get(key)
        if not isinstance(value, str) or not value.strip():
            raise InvalidOpenApiDocumentError(f"{key} must be a non-empty string.")
        return value.strip()
