import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Workspace } from "../workspaces/types";
import { ProjectWorkspace } from "./ProjectWorkspace";

const workspace: Workspace = {
  id: "00000000-0000-4000-8000-000000000001",
  key: "ERP",
  name: "ERP Workspace",
  description: "ERP documentation boundary",
  status: "ACTIVE",
  created_at: "2026-07-29T00:00:00Z",
  updated_at: "2026-07-30T00:00:00Z",
};

const archivedProject = {
  id: "11111111-1111-4111-8111-111111111111",
  key: "DOCS",
  name: "Documentation Platform",
  description: "Source-backed documentation",
  workspace_id: workspace.id,
  ownership_type: "TEAM",
  workspace_type: "ENTERPRISE",
  status: "ARCHIVED",
  created_at: "2026-07-29T00:00:00Z",
  updated_at: "2026-08-06T00:00:00Z",
} as const;

function getRequestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }
  return input instanceof URL ? input.href : input.url;
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ProjectWorkspace", () => {
  it("creates a project inside the selected workspace", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = getRequestUrl(input);
      if (
        url.endsWith(`/api/workspaces/${workspace.id}/projects`) &&
        init?.method === "POST"
      ) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              id: "11db0f9f-557f-4b0b-b962-74bb58ca6f4b",
              key: "ERP-CORE",
              name: "ERP Core",
              description: "Source-backed ERP documentation",
              workspace_id: workspace.id,
              ownership_type: "TEAM",
              workspace_type: "ENTERPRISE",
              status: "ACTIVE",
              created_at: "2026-07-29T00:00:00+00:00",
              updated_at: "2026-07-29T00:00:00+00:00",
            }),
            { status: 201 },
          ),
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
      );
    });

    render(<ProjectWorkspace workspace={workspace} />);
    await waitFor(() =>
      expect(screen.getByText("No projects in this workspace")).toBeInTheDocument(),
    );

    fireEvent.change(screen.getByLabelText("Project name"), {
      target: { value: "ERP Core" },
    });
    fireEvent.change(screen.getByLabelText("Project key"), {
      target: { value: "erp-core" },
    });
    fireEvent.change(screen.getByLabelText("Description"), {
      target: { value: "Source-backed ERP documentation" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create project" }));

    const projectRow = (await screen.findByText("ERP Core")).closest("tr");
    expect(projectRow).not.toBeNull();

    const renderedRow = within(projectRow as HTMLElement);
    expect(renderedRow.getByText("ERP-CORE")).toBeInTheDocument();
    expect(renderedRow.getByText("Team")).toBeInTheDocument();
  });

  it("shows an actionable loading error", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("offline"));

    render(<ProjectWorkspace workspace={workspace} />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Projects could not be loaded");
      expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    });
  });

  it("opens archived projects for read-only inspection", async () => {
    const onOpenProject = vi.fn();
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ items: [archivedProject], total: 1 }), { status: 200 }),
    );

    render(
      <ProjectWorkspace
        workspace={workspace}
        onOpenProject={onOpenProject}
      />,
    );

    const projectRow = (await screen.findByText("Documentation Platform")).closest("tr");
    expect(projectRow).not.toBeNull();

    const renderedRow = within(projectRow as HTMLElement);
    const openButton = renderedRow.getByRole("button", {
      name: "View Documentation Platform workbench",
    });
    expect(openButton).toBeEnabled();

    fireEvent.click(openButton);

    expect(onOpenProject).toHaveBeenCalledWith(archivedProject);
    expect(renderedRow.getByRole("button", { name: "Archived" })).toBeDisabled();
  });

  it("keeps archived workspaces read-only", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
    );

    render(
      <ProjectWorkspace
        workspace={{ ...workspace, status: "ARCHIVED" }}
      />,
    );

    await waitFor(() =>
      expect(screen.getByText(/Existing project evidence remains read-only/)).toBeInTheDocument(),
    );
    expect(screen.getByRole("button", { name: "Create project" })).toBeDisabled();
  });
});
