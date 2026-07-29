from tdp.modules.catalog.infrastructure.openapi_parser import (
    DeterministicOpenApiCatalogParser,
)


def test_parser_normalizes_operations_schemas_and_evidence() -> None:
    content = b"""openapi: 3.1.0
info:
  title: Commerce API
  version: 1.0.0
security:
  - OAuth2: [orders.write]
paths:
  /orders:
    post:
      operationId: createOrder
      summary: Create order
      tags: [Orders]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateOrderRequest'
      responses:
        '201':
          description: Created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Order'
components:
  schemas:
    CreateOrderRequest:
      type: object
      required: [customerId]
      properties:
        customerId:
          type: string
    Order:
      type: object
      required: [id]
      properties:
        id:
          type: string
"""

    catalog = DeterministicOpenApiCatalogParser().parse(content)

    assert len(catalog.operations) == 1
    operation = catalog.operations[0]
    assert operation.method == "POST"
    assert operation.path == "/orders"
    assert operation.operation_id == "createOrder"
    assert operation.security_schemes == ("OAuth2",)
    assert operation.request_body is not None
    assert operation.request_body.schema_references == ("#/components/schemas/CreateOrderRequest",)
    assert operation.responses[0].schema_references == ("#/components/schemas/Order",)
    assert operation.source_pointer == "#/paths/~1orders/post"

    assert [schema.name for schema in catalog.schemas] == [
        "CreateOrderRequest",
        "Order",
    ]
    assert catalog.schemas[0].required_fields == ("customerId",)
