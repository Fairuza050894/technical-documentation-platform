from uuid import uuid4

from tdp.modules.catalog.domain.model import (
    ApiOperation,
    ApiPayload,
    ApiResponse,
    ApiSchema,
    ApiSchemaProperty,
    SynchronizationId,
)
from tdp.modules.changes.domain.model import (
    ChangeKind,
    ChangeSeverity,
    DeterministicCatalogComparator,
)


def operation(
    run_id: SynchronizationId,
    method: str,
    path: str,
    responses: tuple[str, ...],
) -> ApiOperation:
    return ApiOperation(
        synchronization_id=run_id,
        project_id="project",
        source_id="source",
        method=method,
        path=path,
        operation_id="operation",
        summary="",
        description="",
        tags=(),
        deprecated=False,
        security_schemes=(),
        parameters=(),
        request_body=ApiPayload(
            True,
            ("application/json",),
            ("reference",),
            ("#/Request",),
        ),
        responses=tuple(ApiResponse(code, "", (), (), ()) for code in responses),
        source_pointer=f"#/paths/{path}/{method.lower()}",
    )


def schema(run_id: SynchronizationId, required: tuple[str, ...]) -> ApiSchema:
    return ApiSchema(
        synchronization_id=run_id,
        project_id="project",
        source_id="source",
        name="Order",
        schema_type="object",
        description="",
        required_fields=required,
        properties=tuple(
            ApiSchemaProperty(name, "string", "", name in required, "", "")
            for name in ("id", "deliveryType")
        ),
        source_pointer="#/components/schemas/Order",
    )


def test_comparator_classifies_breaking_and_non_breaking_changes() -> None:
    baseline_id = SynchronizationId(uuid4())
    target_id = SynchronizationId(uuid4())
    result = DeterministicCatalogComparator().compare(
        project_id="project",
        baseline_run_id=str(baseline_id),
        target_run_id=str(target_id),
        baseline_operations=[operation(baseline_id, "POST", "/orders", ("201", "400"))],
        target_operations=[
            operation(target_id, "POST", "/orders", ("201", "422")),
            operation(target_id, "POST", "/orders/validate", ("204",)),
        ],
        baseline_schemas=[schema(baseline_id, ("id",))],
        target_schemas=[schema(target_id, ("id", "deliveryType"))],
    )

    assert result.breaking_total == 2
    assert any(
        item.entity_key == "POST /orders"
        and item.kind is ChangeKind.MODIFIED
        and item.severity is ChangeSeverity.BREAKING
        for item in result.changes
    )
    assert any(
        item.entity_key == "POST /orders/validate"
        and item.kind is ChangeKind.ADDED
        and item.severity is ChangeSeverity.NON_BREAKING
        for item in result.changes
    )
    assert any(
        item.entity_key == "Order"
        and item.details["new_required_fields"] == ["deliveryType"]
        for item in result.changes
    )
