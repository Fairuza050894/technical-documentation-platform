import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiCatalogWorkspace } from "./ApiCatalogWorkspace";

function getRequestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }
  return input instanceof URL ? input.href : input.url;
}

afterEach(() => {
  vi.restoreAllMocks();
});

const project = {
  id: "5e742f10-bdc0-4a24-b6dd-3002e875cc85",
  key: "DOCS",
  name: "Documentation Platform",
  description: "",
  workspace_type: "PERSONAL",
  status: "ACTIVE",
  created_at: "2026-07-29T00:00:00+00:00",
  updated_at: "2026-07-29T00:00:00+00:00",
};

const source = {
  id: "6e742f10-bdc0-4a24-b6dd-3002e875cc86",
  project_id: project.id,
  name: "Commerce OpenAPI",
  source_type: "OPENAPI_FILE",
  status: "READY",
  original_file_name: "commerce.yaml",
  media_type: "YAML",
  checksum: "a".repeat(64),
  openapi_version: "3.1.0",
  api_title: "Commerce API",
  api_version: "1.0.0",
  path_count: 1,
  operation_count: 1,
  created_at: "2026-07-29T00:00:00+00:00",
  updated_at: "2026-07-29T00:00:00+00:00",
};

const catalog = {
  runs: [{
    id: "7e742f10-bdc0-4a24-b6dd-3002e875cc87",
    project_id: project.id,
    source_id: source.id,
    source_checksum: source.checksum,
    status: "COMPLETED",
    operation_count: 1,
    schema_count: 1,
    error_code: "",
    error_message: "",
    started_at: "2026-07-29T00:00:00+00:00",
    completed_at: "2026-07-29T00:00:01+00:00",
  }],
  operations: [{
    synchronization_id: "7e742f10-bdc0-4a24-b6dd-3002e875cc87",
    project_id: project.id,
    source_id: source.id,
    method: "POST",
    path: "/orders",
    operation_id: "createOrder",
    summary: "Create order",
    description: "",
    tags: ["Orders"],
    deprecated: false,
    security_schemes: ["OAuth2"],
    parameters: [],
    request_body: {
      required: true,
      media_types: ["application/json"],
      schema_types: ["reference"],
      schema_references: ["#/components/schemas/CreateOrderRequest"],
    },
    responses: [{
      status_code: "201",
      description: "Created",
      media_types: ["application/json"],
      schema_types: ["reference"],
      schema_references: ["#/components/schemas/Order"],
    }],
    source_pointer: "#/paths/~1orders/post",
  }],
  schemas: [{
    synchronization_id: "7e742f10-bdc0-4a24-b6dd-3002e875cc87",
    project_id: project.id,
    source_id: source.id,
    name: "Order",
    schema_type: "object",
    description: "",
    required_fields: ["id"],
    properties: [],
    source_pointer: "#/components/schemas/Order",
  }],
  operation_total: 1,
  schema_total: 1,
};

describe("ApiCatalogWorkspace", () => {
  it("shows normalized operations and source evidence", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = getRequestUrl(input);
      if (url.endsWith("/api/projects")) {
        return Promise.resolve(new Response(JSON.stringify({ items: [project], total: 1 })));
      }
      if (url.includes("/sources")) {
        return Promise.resolve(new Response(JSON.stringify({ items: [source], total: 1 })));
      }
      return Promise.resolve(new Response(JSON.stringify(catalog)));
    });

    render(<ApiCatalogWorkspace />);

    await waitFor(() => expect(screen.getByText("/orders")).toBeInTheDocument());
    expect(screen.getByText("Create order")).toBeInTheDocument();
    expect(screen.getByText("#/paths/~1orders/post")).toBeInTheDocument();
    expect(screen.getByText("Order")).toBeInTheDocument();
  });

  it("synchronizes the selected source", async () => {
    let synchronized = false;
    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = getRequestUrl(input);
      if (url.endsWith("/api/projects")) {
        return Promise.resolve(new Response(JSON.stringify({ items: [project], total: 1 })));
      }
      if (url.endsWith(`/api/projects/${project.id}/sources`)) {
        return Promise.resolve(new Response(JSON.stringify({ items: [source], total: 1 })));
      }
      if (url.endsWith(`/api/sources/${source.id}/synchronizations`) && init?.method === "POST") {
        synchronized = true;
        return Promise.resolve(new Response(JSON.stringify(catalog.runs[0]), { status: 201 }));
      }
      return Promise.resolve(new Response(JSON.stringify(synchronized ? catalog : {
        runs: [],
        operations: [],
        schemas: [],
        operation_total: 0,
        schema_total: 0,
      })));
    });

    render(<ApiCatalogWorkspace />);
    await waitFor(() => expect(screen.getByText("Synchronize a source")).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText("Source"), { target: { value: source.id } });
    fireEvent.click(screen.getByRole("button", { name: "Synchronize source" }));

    await waitFor(() => expect(screen.getByText("/orders")).toBeInTheDocument());
  });
});
