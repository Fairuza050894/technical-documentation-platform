import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ProjectWorkspace } from "./ProjectWorkspace";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ProjectWorkspace", () => {
  it("creates a project and adds it to the registry", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((_input, init) => {
      if (init?.method === "POST") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              id: "11db0f9f-557f-4b0b-b962-74bb58ca6f4b",
              key: "DOCS",
              name: "Documentation Platform",
              description: "Source-backed documentation",
              workspace_type: "PERSONAL",
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

    render(<ProjectWorkspace />);
    await waitFor(() => expect(screen.getByText("No projects yet")).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText("Project name"), {
      target: { value: "Documentation Platform" },
    });
    fireEvent.change(screen.getByLabelText("Project key"), {
      target: { value: "docs" },
    });
    fireEvent.change(screen.getByLabelText("Description"), {
      target: { value: "Source-backed documentation" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create project" }));

    await waitFor(() => {
      expect(screen.getByText("Documentation Platform")).toBeInTheDocument();
      expect(screen.getByText("DOCS")).toBeInTheDocument();
    });
  });

  it("shows an actionable loading error", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("offline"));

    render(<ProjectWorkspace />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Projects could not be loaded");
      expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    });
  });
});
