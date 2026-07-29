from collections.abc import Mapping, Sequence
from typing import cast

import yaml

from tdp.modules.catalog.application.ports import (
    ParsedCatalog,
    ParsedOperation,
    ParsedSchema,
)
from tdp.modules.catalog.domain.errors import InvalidCatalogDocumentError
from tdp.modules.catalog.domain.model import (
    ApiParameter,
    ApiPayload,
    ApiResponse,
    ApiSchemaProperty,
)

_HTTP_METHODS = ("delete", "get", "head", "options", "patch", "post", "put", "trace")


class DeterministicOpenApiCatalogParser:
    def parse(self, content: bytes) -> ParsedCatalog:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InvalidCatalogDocumentError(
                "OpenAPI catalog source must use UTF-8 encoding."
            ) from exc

        root = self._load_root(text)
        paths = self._mapping(root.get("paths"), "paths")
        root_security = self._security_names(root.get("security"))

        operations: list[ParsedOperation] = []
        for path in sorted(paths):
            path_item = self._mapping(paths[path], f"path item {path}")
            path_parameters = self._parameter_list(
                root,
                path_item.get("parameters"),
                pointer=f"#/paths/{self._pointer_token(path)}/parameters",
            )
            for method in _HTTP_METHODS:
                operation_value = path_item.get(method)
                if operation_value is None:
                    continue
                operation = self._mapping(operation_value, f"{method.upper()} {path}")
                operation_pointer = f"#/paths/{self._pointer_token(path)}/{method}"
                operation_parameters = self._parameter_list(
                    root,
                    operation.get("parameters"),
                    pointer=f"{operation_pointer}/parameters",
                )
                parameters = self._merge_parameters(path_parameters, operation_parameters)
                security_value = (
                    operation.get("security") if "security" in operation else root.get("security")
                )
                security_schemes = self._security_names(security_value)
                if "security" not in operation:
                    security_schemes = root_security

                operations.append(
                    ParsedOperation(
                        method=method.upper(),
                        path=path,
                        operation_id=self._text(operation.get("operationId")),
                        summary=self._text(operation.get("summary")),
                        description=self._text(operation.get("description")),
                        tags=self._string_tuple(operation.get("tags")),
                        deprecated=operation.get("deprecated") is True,
                        security_schemes=security_schemes,
                        parameters=parameters,
                        request_body=self._payload(
                            root,
                            operation.get("requestBody"),
                            pointer=f"{operation_pointer}/requestBody",
                        ),
                        responses=self._responses(
                            root,
                            operation.get("responses"),
                            pointer=f"{operation_pointer}/responses",
                        ),
                        source_pointer=operation_pointer,
                    )
                )

        schemas = self._schemas(root)
        return ParsedCatalog(operations=tuple(operations), schemas=schemas)

    def _load_root(self, text: str) -> Mapping[str, object]:
        try:
            document: object = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise InvalidCatalogDocumentError(
                "OpenAPI catalog source contains invalid JSON or YAML syntax."
            ) from exc
        root = self._mapping(document, "OpenAPI document root")
        version = self._text(root.get("openapi"))
        if not version.startswith(("3.0.", "3.1.")):
            raise InvalidCatalogDocumentError(
                "API catalog synchronization supports OpenAPI 3.0.x and 3.1.x."
            )
        return root

    def _schemas(self, root: Mapping[str, object]) -> tuple[ParsedSchema, ...]:
        components_value = root.get("components")
        if components_value is None:
            return ()
        components = self._mapping(components_value, "components")
        schemas_value = components.get("schemas")
        if schemas_value is None:
            return ()
        schemas = self._mapping(schemas_value, "components.schemas")

        results: list[ParsedSchema] = []
        for name in sorted(schemas):
            schema = self._resolved_mapping(root, schemas[name], f"schema {name}")
            required_fields = frozenset(self._string_tuple(schema.get("required")))
            properties_value = schema.get("properties")
            properties_mapping = (
                self._mapping(properties_value, f"schema {name} properties")
                if properties_value is not None
                else {}
            )
            properties: list[ApiSchemaProperty] = []
            for property_name in sorted(properties_mapping):
                property_schema = self._resolved_mapping(
                    root,
                    properties_mapping[property_name],
                    f"schema property {name}.{property_name}",
                )
                properties.append(
                    ApiSchemaProperty(
                        name=property_name,
                        schema_type=self._schema_type(property_schema),
                        schema_format=self._text(property_schema.get("format")),
                        required=property_name in required_fields,
                        reference=self._reference(properties_mapping[property_name]),
                        description=self._text(property_schema.get("description")),
                    )
                )

            results.append(
                ParsedSchema(
                    name=name,
                    schema_type=self._schema_type(schema),
                    description=self._text(schema.get("description")),
                    required_fields=tuple(sorted(required_fields)),
                    properties=tuple(properties),
                    source_pointer=f"#/components/schemas/{self._pointer_token(name)}",
                )
            )
        return tuple(results)

    def _parameter_list(
        self,
        root: Mapping[str, object],
        value: object,
        *,
        pointer: str,
    ) -> tuple[ApiParameter, ...]:
        if value is None:
            return ()
        items = self._sequence(value, pointer)
        parameters: list[ApiParameter] = []
        for index, item in enumerate(items):
            parameter = self._resolved_mapping(root, item, f"{pointer}/{index}")
            schema_value = parameter.get("schema")
            schema = (
                self._resolved_mapping(root, schema_value, f"{pointer}/{index}/schema")
                if schema_value is not None
                else {}
            )
            parameters.append(
                ApiParameter(
                    name=self._required_text(parameter, "name", f"{pointer}/{index}"),
                    location=self._required_text(parameter, "in", f"{pointer}/{index}"),
                    required=parameter.get("required") is True,
                    schema_type=self._schema_type(schema),
                    schema_format=self._text(schema.get("format")),
                    schema_reference=self._reference(schema_value),
                )
            )
        return tuple(parameters)

    @staticmethod
    def _merge_parameters(
        path_parameters: tuple[ApiParameter, ...],
        operation_parameters: tuple[ApiParameter, ...],
    ) -> tuple[ApiParameter, ...]:
        merged = {(parameter.name, parameter.location): parameter for parameter in path_parameters}
        merged.update(
            {(parameter.name, parameter.location): parameter for parameter in operation_parameters}
        )
        return tuple(merged[key] for key in sorted(merged, key=lambda item: (item[1], item[0])))

    def _payload(
        self,
        root: Mapping[str, object],
        value: object,
        *,
        pointer: str,
    ) -> ApiPayload | None:
        if value is None:
            return None
        payload = self._resolved_mapping(root, value, pointer)
        content_value = payload.get("content")
        content = self._mapping(content_value, f"{pointer}/content") if content_value else {}
        schema_types: set[str] = set()
        schema_references: set[str] = set()
        for media_type in sorted(content):
            media = self._mapping(content[media_type], f"{pointer}/content/{media_type}")
            schema_value = media.get("schema")
            if schema_value is None:
                continue
            schema = self._resolved_mapping(root, schema_value, f"{pointer}/content/{media_type}")
            schema_type = self._schema_type(schema)
            if schema_type:
                schema_types.add(schema_type)
            schema_references.update(self._schema_references(schema_value))

        return ApiPayload(
            required=payload.get("required") is True,
            media_types=tuple(sorted(content)),
            schema_types=tuple(sorted(schema_types)),
            schema_references=tuple(sorted(schema_references)),
        )

    def _responses(
        self,
        root: Mapping[str, object],
        value: object,
        *,
        pointer: str,
    ) -> tuple[ApiResponse, ...]:
        if value is None:
            return ()
        responses = self._mapping(value, pointer)
        results: list[ApiResponse] = []
        for status_code in sorted(responses):
            response = self._resolved_mapping(
                root,
                responses[status_code],
                f"{pointer}/{status_code}",
            )
            content_value = response.get("content")
            content = (
                self._mapping(content_value, f"{pointer}/{status_code}/content")
                if content_value
                else {}
            )
            schema_types: set[str] = set()
            schema_references: set[str] = set()
            for media_type in sorted(content):
                media = self._mapping(
                    content[media_type],
                    f"{pointer}/{status_code}/content/{media_type}",
                )
                schema_value = media.get("schema")
                if schema_value is None:
                    continue
                schema = self._resolved_mapping(
                    root,
                    schema_value,
                    f"{pointer}/{status_code}/content/{media_type}/schema",
                )
                schema_type = self._schema_type(schema)
                if schema_type:
                    schema_types.add(schema_type)
                schema_references.update(self._schema_references(schema_value))

            results.append(
                ApiResponse(
                    status_code=status_code,
                    description=self._text(response.get("description")),
                    media_types=tuple(sorted(content)),
                    schema_types=tuple(sorted(schema_types)),
                    schema_references=tuple(sorted(schema_references)),
                )
            )
        return tuple(results)

    def _security_names(self, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        requirements = self._sequence(value, "security")
        names: set[str] = set()
        for requirement in requirements:
            if not isinstance(requirement, Mapping):
                raise InvalidCatalogDocumentError("security entries must be objects.")
            names.update(str(name) for name in requirement)
        return tuple(sorted(names))

    def _resolved_mapping(
        self,
        root: Mapping[str, object],
        value: object,
        label: str,
    ) -> Mapping[str, object]:
        mapping = self._mapping(value, label)
        reference = mapping.get("$ref")
        if isinstance(reference, str):
            return self._resolve_reference(root, reference)
        return mapping

    def _resolve_reference(
        self,
        root: Mapping[str, object],
        reference: str,
    ) -> Mapping[str, object]:
        if not reference.startswith("#/"):
            raise InvalidCatalogDocumentError(
                f"External reference {reference} is not supported in MVP 1."
            )
        current: object = root
        for token in reference[2:].split("/"):
            key = token.replace("~1", "/").replace("~0", "~")
            mapping = self._mapping(current, reference)
            if key not in mapping:
                raise InvalidCatalogDocumentError(f"Reference {reference} could not be resolved.")
            current = mapping[key]
        return self._mapping(current, reference)

    def _schema_references(self, value: object) -> set[str]:
        if not isinstance(value, Mapping):
            return set()
        references: set[str] = set()
        reference = value.get("$ref")
        if isinstance(reference, str):
            references.add(reference)
        for key in ("allOf", "anyOf", "oneOf"):
            collection = value.get(key)
            if isinstance(collection, Sequence) and not isinstance(
                collection, (str, bytes, bytearray)
            ):
                for item in collection:
                    references.update(self._schema_references(item))
        items = value.get("items")
        if items is not None:
            references.update(self._schema_references(items))
        return references

    def _schema_type(self, schema: Mapping[str, object]) -> str:
        schema_type = self._text(schema.get("type"))
        if schema_type:
            return schema_type
        if "$ref" in schema:
            return "reference"
        if "allOf" in schema:
            return "allOf"
        if "oneOf" in schema:
            return "oneOf"
        if "anyOf" in schema:
            return "anyOf"
        return ""

    @staticmethod
    def _reference(value: object) -> str:
        if isinstance(value, Mapping):
            reference = value.get("$ref")
            return reference if isinstance(reference, str) else ""
        return ""

    @staticmethod
    def _mapping(value: object, label: str) -> Mapping[str, object]:
        if not isinstance(value, Mapping):
            raise InvalidCatalogDocumentError(f"{label} must be an object.")
        return cast(Mapping[str, object], value)

    @staticmethod
    def _sequence(value: object, label: str) -> Sequence[object]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
            raise InvalidCatalogDocumentError(f"{label} must be an array.")
        return cast(Sequence[object], value)

    @staticmethod
    def _text(value: object) -> str:
        return value.strip() if isinstance(value, str) else ""

    def _required_text(
        self,
        mapping: Mapping[str, object],
        key: str,
        label: str,
    ) -> str:
        value = self._text(mapping.get(key))
        if not value:
            raise InvalidCatalogDocumentError(f"{label}.{key} must be a non-empty string.")
        return value

    def _string_tuple(self, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        return tuple(
            sorted(
                {
                    item.strip()
                    for item in self._sequence(value, "string array")
                    if isinstance(item, str) and item.strip()
                }
            )
        )

    @staticmethod
    def _pointer_token(value: str) -> str:
        return value.replace("~", "~0").replace("/", "~1")
