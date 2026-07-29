import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ChangesWorkspace } from "./ChangesWorkspace";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ChangesWorkspace", () => {
  it("compares completed snapshots and shows breaking changes", async () => {
    const projectId = "11111111-1111-4111-8111-111111111111";
    const baselineId = "22222222-2222-4222-8222-222222222222";
    const targetId = "33333333-3333-4333-8333-333333333333";
    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
      if (url.endsWith("/api/projects")) {
        return Promise.resolve(new Response(JSON.stringify({
          items: [{ id: projectId, key: "DOCS", name: "Documentation", description: "", workspace_type: "PERSONAL", status: "ACTIVE", created_at: "", updated_at: "" }],
          total: 1,
        })));
      }
      if (url.endsWith(`/api/projects/${projectId}/sources`)) {
        return Promise.resolve(new Response(JSON.stringify({
          items: [
            { id: "source-v1", project_id: projectId, name: "Commerce v1", status: "READY" },
            { id: "source-v2", project_id: projectId, name: "Commerce v2", status: "READY" },
          ],
          total: 2,
        })));
      }
      if (url.endsWith("/api/sources/source-v1/synchronizations")) {
        return Promise.resolve(new Response(JSON.stringify({ items: [{ id: baselineId, status: "COMPLETED", started_at: "2026-07-28T00:00:00Z" }], total: 1 })));
      }
      if (url.endsWith("/api/sources/source-v2/synchronizations")) {
        return Promise.resolve(new Response(JSON.stringify({ items: [{ id: targetId, status: "COMPLETED", started_at: "2026-07-29T00:00:00Z" }], total: 1 })));
      }
      if (url.endsWith(`/api/projects/${projectId}/comparisons`) && init?.method === "POST") {
        return Promise.resolve(new Response(JSON.stringify({
          project_id: projectId,
          baseline_run_id: baselineId,
          target_run_id: targetId,
          total: 1,
          breaking_total: 1,
          changes: [{
            entity_type: "SCHEMA",
            entity_key: "CreateOrderRequest",
            kind: "MODIFIED",
            severity: "BREAKING",
            summary: "Schema CreateOrderRequest changed.",
            before_pointer: "#/components/schemas/CreateOrderRequest",
            after_pointer: "#/components/schemas/CreateOrderRequest",
            details: { new_required_fields: ["deliveryType"] },
          }],
        })));
      }
      return Promise.resolve(new Response(JSON.stringify({ items: [], total: 0 })));
    });

    render(<ChangesWorkspace />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Compare snapshots" })).toBeEnabled());
    fireEvent.click(screen.getByRole("button", { name: "Compare snapshots" }));
    await waitFor(() => expect(screen.getByText("CreateOrderRequest")).toBeInTheDocument());
    expect(screen.getByText("1 breaking changes require review.")).toBeInTheDocument();
  });
});
