import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Project } from "../projects/types";
import { FeatureWorkspace } from "./FeatureWorkspace";

const workspaceId = "00000000-0000-4000-8000-000000000001";
const projectId = "11111111-1111-4111-8111-111111111111";
const featureId = "33333333-3333-4333-8333-333333333333";

const project: Project = {
  id: projectId,
  key: "ERP-CORE",
  name: "ERP Core",
  description: "ERP capability boundary",
  workspace_id: workspaceId,
  ownership_type: "TEAM",
  workspace_type: "ENTERPRISE",
  status: "ACTIVE",
  created_at: "2026-08-01T00:00:00Z",
  updated_at: "2026-08-01T00:00:00Z",
};

function getRequestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }
  return input instanceof URL ? input.href : input.url;
}

function featureRecord(status: "ACTIVE" | "ARCHIVED" = "ACTIVE") {
  return {
    id: featureId,
    project_id: projectId,
    key: "PURCHASE-ORDER",
    name: "Purchase Order",
    description: "Purchase order lifecycle",
    kind: "FEATURE",
    owner: "ERP Product Team",
    status,
    documentation_coverage: {
      required_total: 4,
      available_required: 0,
      missing_required: 4,
      optional_total: 4,
    },
    created_at: "2026-08-01T00:00:00Z",
    updated_at: "2026-08-01T00:00:00Z",
  };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("FeatureWorkspace", () => {
  it("creates a capability and opens its deterministic documentation map", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = getRequestUrl(input);
      if (url.endsWith(`/api/workspaces/${workspaceId}/projects/${projectId}/features`)) {
        if (init?.method === "POST") {
          return Promise.resolve(
            new Response(JSON.stringify(featureRecord()), { status: 201 }),
          );
        }
        return Promise.resolve(
          new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
        );
      }
      return Promise.resolve(new Response(JSON.stringify({}), { status: 200 }));
    });
    const openFeature = vi.fn();

    render(
      <FeatureWorkspace
        workspaceId={workspaceId}
        project={project}
        selectedFeatureId={null}
        onOpenFeature={openFeature}
        onCloseFeature={vi.fn()}
      />,
    );

    expect(await screen.findByText("No features or modules yet")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Name"), {
      target: { value: "Purchase Order" },
    });
    fireEvent.change(screen.getByLabelText("Feature key"), {
      target: { value: "purchase-order" },
    });
    fireEvent.change(screen.getByLabelText("Owner"), {
      target: { value: "ERP Product Team" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create capability" }));

    await waitFor(() => {
      expect(openFeature).toHaveBeenCalledWith(featureId);
    });
    const row = (await screen.findByText("Purchase Order")).closest("tr");
    expect(row).not.toBeNull();
    expect(within(row as HTMLElement).getByText("Feature")).toBeInTheDocument();
    expect(within(row as HTMLElement).getByText("0 / 4")).toBeInTheDocument();
  });

  it("renders required and optional coverage from the policy map", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = getRequestUrl(input);
      if (url.endsWith(`/api/workspaces/${workspaceId}/projects/${projectId}/features`)) {
        return Promise.resolve(
          new Response(JSON.stringify({ items: [featureRecord()], total: 1 }), {
            status: 200,
          }),
        );
      }
      if (url.endsWith(`/features/${featureId}/documentation-map`)) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              feature_id: featureId,
              policy_key: "feature-documentation-baseline-v1",
              total: 2,
              items: [
                {
                  document_type: "BUSINESS_REQUIREMENT",
                  requirement: "REQUIRED",
                  coverage_status: "MISSING",
                  document_id: null,
                  policy_key: "feature-documentation-baseline-v1",
                  created_at: "2026-08-01T00:00:00Z",
                  updated_at: "2026-08-01T00:00:00Z",
                },
                {
                  document_type: "API_DOCUMENTATION",
                  requirement: "OPTIONAL",
                  coverage_status: "PLANNED",
                  document_id: null,
                  policy_key: "feature-documentation-baseline-v1",
                  created_at: "2026-08-01T00:00:00Z",
                  updated_at: "2026-08-01T00:00:00Z",
                },
              ],
            }),
            { status: 200 },
          ),
        );
      }
      return Promise.resolve(new Response(JSON.stringify({}), { status: 200 }));
    });

    render(
      <FeatureWorkspace
        workspaceId={workspaceId}
        project={project}
        selectedFeatureId={featureId}
        onOpenFeature={vi.fn()}
        onCloseFeature={vi.fn()}
      />,
    );

    expect(await screen.findByRole("heading", { name: "Purchase Order" })).toBeInTheDocument();
    expect(await screen.findByText("Business requirement")).toBeInTheDocument();
    expect(screen.getByText("Required by baseline")).toBeInTheDocument();
    expect(screen.getByText("API documentation")).toBeInTheDocument();
    expect(screen.getByText("Optional baseline coverage")).toBeInTheDocument();
    expect(screen.getByText("Missing")).toBeInTheDocument();
    expect(screen.getByText("Planned")).toBeInTheDocument();
  });

  it("keeps capability mutation read-only for archived projects", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ items: [featureRecord()], total: 1 }), {
        status: 200,
      }),
    );

    render(
      <FeatureWorkspace
        workspaceId={workspaceId}
        project={{ ...project, status: "ARCHIVED" }}
        selectedFeatureId={null}
        onOpenFeature={vi.fn()}
        onCloseFeature={vi.fn()}
      />,
    );

    expect(
      await screen.findByText("Archived projects keep their feature evidence read-only."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create capability" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Archive" })).toBeDisabled();
  });
});
