import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { WorkspaceRegistry } from "./WorkspaceRegistry";

const defaultWorkspace = {
  id: "00000000-0000-4000-8000-000000000001",
  key: "GENERAL",
  name: "General Workspace",
  description: "Migrated projects",
  status: "ACTIVE" as const,
  created_at: "2026-07-29T00:00:00Z",
  updated_at: "2026-07-30T00:00:00Z",
};

function getRequestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }
  return input instanceof URL ? input.href : input.url;
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("WorkspaceRegistry", () => {
  it("creates and selects a workspace", async () => {
    const selectWorkspace = vi.fn();
    const changed = vi.fn();
    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = getRequestUrl(input);
      if (url.endsWith("/api/workspaces") && init?.method === "POST") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...defaultWorkspace,
              id: "22222222-2222-4222-8222-222222222222",
              key: "ERP",
              name: "ERP Workspace",
              description: "ERP systems",
            }),
            { status: 201 },
          ),
        );
      }
      if (url.endsWith("/api/workspaces")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({ items: [defaultWorkspace], total: 1 }),
            { status: 200 },
          ),
        );
      }
      throw new Error(`Unexpected request: ${url}`);
    });

    render(
      <WorkspaceRegistry
        activeWorkspaceId={defaultWorkspace.id}
        onSelectWorkspace={selectWorkspace}
        onWorkspacesChanged={changed}
      />,
    );

    await screen.findByText("General Workspace");
    fireEvent.change(screen.getByLabelText("Workspace name"), {
      target: { value: "ERP Workspace" },
    });
    fireEvent.change(screen.getByLabelText("Workspace key"), {
      target: { value: "erp" },
    });
    fireEvent.change(screen.getByLabelText("Description"), {
      target: { value: "ERP systems" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create workspace" }));

    await waitFor(() => {
      expect(screen.getByText("ERP Workspace")).toBeInTheDocument();
    });
    expect(selectWorkspace).toHaveBeenCalledWith(
      expect.objectContaining({ key: "ERP", name: "ERP Workspace" }),
    );
    expect(changed).toHaveBeenLastCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ key: "GENERAL" }),
        expect.objectContaining({ key: "ERP" }),
      ]),
    );
  });

  it("protects the default workspace from archive", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ items: [defaultWorkspace], total: 1 }), {
        status: 200,
      }),
    );

    render(
      <WorkspaceRegistry
        activeWorkspaceId={defaultWorkspace.id}
        onSelectWorkspace={vi.fn()}
        onWorkspacesChanged={vi.fn()}
      />,
    );

    await screen.findByText("General Workspace");
    expect(screen.getByRole("button", { name: "Archive" })).toBeDisabled();
  });
});
