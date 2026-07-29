import pytest

from tdp.modules.sources.domain.errors import (
    InvalidOpenApiDocumentError,
    UnsupportedOpenApiVersionError,
)
from tdp.modules.sources.domain.model import SourceFileName, SourceMediaType
from tdp.modules.sources.infrastructure.openapi_inspector import DeterministicOpenApiInspector


def test_inspector_reads_openapi_json_deterministically() -> None:
    content = b"""{
      "openapi": "3.1.0",
      "info": {"title": "Commerce API", "version": "1.0.0"},
      "paths": {
        "/orders": {"get": {}, "post": {}},
        "/orders/{orderId}": {"get": {}}
      }
    }"""

    result = DeterministicOpenApiInspector().inspect(
        SourceFileName("commerce.json"),
        content,
    )

    assert result.media_type is SourceMediaType.JSON
    assert result.api_title == "Commerce API"
    assert result.path_count == 2
    assert result.operation_count == 3
    assert len(result.checksum) == 64


def test_inspector_reads_openapi_yaml() -> None:
    content = b"""openapi: 3.0.3
info:
  title: Delivery API
  version: 2.1.0
paths:
  /deliveries:
    post: {}
"""

    result = DeterministicOpenApiInspector().inspect(
        SourceFileName("delivery.yaml"),
        content,
    )

    assert result.media_type is SourceMediaType.YAML
    assert result.openapi_version == "3.0.3"
    assert result.operation_count == 1


def test_inspector_rejects_missing_required_structure() -> None:
    with pytest.raises(InvalidOpenApiDocumentError):
        DeterministicOpenApiInspector().inspect(
            SourceFileName("invalid.json"),
            b'{"openapi":"3.1.0"}',
        )


def test_inspector_rejects_unsupported_version() -> None:
    with pytest.raises(UnsupportedOpenApiVersionError):
        DeterministicOpenApiInspector().inspect(
            SourceFileName("legacy.yaml"),
            b"swagger: '2.0'\ninfo:\n  title: Legacy\n  version: 1.0.0\npaths: {}\n",
        )
