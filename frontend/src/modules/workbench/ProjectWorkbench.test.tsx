import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ProjectWorkbench } from "./ProjectWorkbench";

const workspaceId = "00000000-0000-4000-8000-000000000001";
const projectId = "11111111-1111-4111-8111-111111111111";

function getRequestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }
  return input instanceof URL ? input.href : input.url;
}

function projectRecord(overrideWorkspaceId = workspaceId) {
  return {
    id: projectId,
    key: "DOCS",
    name: "Documentation Platform",
    description: "Source-backed documentation",
    workspace_id: overrideWorkspaceId,
    ownership_type: "TEAM",
    workspace_type: "ENTERPRISE",
    status: "ACTIVE",
    created_at: "2026-07-29T00:00:00Z",
    updated_at: "2026-07-30T00:00:00Z",
  };
}

function featureRecord() {
  return {
    id: "33333333-3333-4333-8333-333333333333",
    project_id: projectId,
    key: "DOCS-CORE",
    name: "Documentation Core",
    description: "Core documentation capability",
    kind: "MODULE",
    owner: "Platform Team",
    status: "ACTIVE",
    documentation_coverage: {
      required_total: 5,
      available_required: 0,
      missing_required: 5,
      optional_total: 3,
    },
    created_at: "2026-08-01T00:00:00Z",
    updated_at: "2026-08-01T00:00:00Z",
  };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ProjectWorkbench", () => {
  it("derives the next action from project evidence", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = getRequestUrl(input);
      if (url.endsWith(`/api/projects/${projectId}`)) {
        return Promise.resolve(
          new Response(JSON.stringify(projectRecord()), { status: 200 }),
        );
      }
      if (url.endsWith(`/api/workspaces/${workspaceId}/projects/${projectId}/features`)) {
        return Promise.resolve(
          new Response(JSON.stringify({ items: [featureRecord()], total: 1 }), { status: 200 }),
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
      );
    });
    const navigateStage = vi.fn();

    render(
      <ProjectWorkbench
        workspaceId={workspaceId}
        projectId={projectId}
        stage="overview"
        featureId={null}
        onNavigateStage={navigateStage}
        onNavigateFeature={vi.fn()}
        onBackToProjects={vi.fn()}
        onProjectResolved={vi.fn()}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Import the first technical source")).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: "Projects" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Open source intake" }));
    expect(navigateStage).toHaveBeenCalledWith("sources");
  });

  it("recommends defining a capability before technical intake", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = getRequestUrl(input);
      if (url.endsWith(`/api/projects/${projectId}`)) {
        return Promise.resolve(
          new Response(JSON.stringify(projectRecord()), { status: 200 }),
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
      );
    });
    const navigateStage = vi.fn();

    render(
      <ProjectWorkbench
        workspaceId={workspaceId}
        projectId={projectId}
        stage="overview"
        featureId={null}
        onNavigateStage={navigateStage}
        onNavigateFeature={vi.fn()}
        onBackToProjects={vi.fn()}
        onProjectResolved={vi.fn()}
      />,
    );

    expect(
      await screen.findByText("Define the first feature or module"),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Open capability registry" }));
    expect(navigateStage).toHaveBeenCalledWith("features");
  });

  it("rejects a project that belongs to another workspace", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = getRequestUrl(input);
      if (url.endsWith(`/api/projects/${projectId}`)) {
        return Promise.resolve(
          new Response(
            JSON.stringify(projectRecord("22222222-2222-4222-8222-222222222222")),
            { status: 200 },
          ),
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
      );
    });

    render(
      <ProjectWorkbench
        workspaceId={workspaceId}
        projectId={projectId}
        stage="overview"
        featureId={null}
        onNavigateStage={vi.fn()}
        onNavigateFeature={vi.fn()}
        onBackToProjects={vi.fn()}
        onProjectResolved={vi.fn()}
      />,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Project not found" })).toBeInTheDocument();
    });
  });

  it("shows an actionable missing-project state", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: "PROJECT_NOT_FOUND",
            message: "Project missing was not found.",
          },
        }),
        { status: 404 },
      ),
    );
    const back = vi.fn();

    render(
      <ProjectWorkbench
        workspaceId={workspaceId}
        projectId="missing"
        stage="overview"
        featureId={null}
        onNavigateStage={vi.fn()}
        onNavigateFeature={vi.fn()}
        onBackToProjects={back}
        onProjectResolved={vi.fn()}
      />,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Project not found" })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: "Open project registry" }));
    expect(back).toHaveBeenCalledOnce();
  });
});
