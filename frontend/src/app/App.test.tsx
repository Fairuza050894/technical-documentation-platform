import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

const projectId = "11111111-1111-4111-8111-111111111111";

function getRequestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }
  return input instanceof URL ? input.href : input.url;
}

function projectRecord() {
  return {
    id: projectId,
    key: "DOCS",
    name: "Documentation Platform",
    description: "Source-backed documentation",
    workspace_type: "PERSONAL",
    status: "ACTIVE",
    created_at: "2026-07-29T00:00:00Z",
    updated_at: "2026-07-30T00:00:00Z",
  };
}

function mockPlatform({ withProject = false }: { withProject?: boolean } = {}): void {
  vi.spyOn(globalThis, "fetch").mockImplementation((input: RequestInfo | URL) => {
    const url = getRequestUrl(input);
    if (url.endsWith("/api/health")) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            status: "ok",
            service: "Technical Documentation Platform",
            version: "0.1.0",
            environment: "development",
          }),
          { status: 200 },
        ),
      );
    }
    if (url.endsWith("/api/projects")) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            items: withProject ? [projectRecord()] : [],
            total: withProject ? 1 : 0,
          }),
          { status: 200 },
        ),
      );
    }
    if (url.endsWith(`/api/projects/${projectId}/sources`)) {
      return Promise.resolve(new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }));
    }
    if (url.endsWith(`/api/projects/${projectId}/documents`)) {
      return Promise.resolve(new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }));
    }
    return Promise.resolve(new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }));
  });
}

beforeEach(() => {
  globalThis.history.replaceState({}, "", "/");
});

afterEach(() => {
  vi.restoreAllMocks();
  globalThis.history.replaceState({}, "", "/");
});

describe("App", () => {
  it("opens Home by default with simplified global navigation", async () => {
    mockPlatform();

    render(<App />);

    expect(screen.getByRole("heading", { name: "Overview" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Home" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.queryByRole("button", { name: "Source registry" })).not.toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Active projects: 0/ })).toBeInTheDocument();
    });
  });

  it("uses the URL when opening the project registry", async () => {
    mockPlatform();

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Projects" }));

    expect(globalThis.location.pathname).toBe("/projects");
    expect(screen.getByRole("heading", { name: "Projects" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("No projects yet")).toBeInTheDocument());
  });

  it("opens a project workbench from the registry", async () => {
    mockPlatform({ withProject: true });

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Projects" }));
    await waitFor(() => expect(screen.getByText("Documentation Platform")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Open Documentation Platform workbench" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Documentation Platform" })).toBeInTheDocument();
    });
    expect(globalThis.location.pathname).toBe(
      `/projects/${projectId}/workbench/overview`,
    );
    expect(screen.getByRole("navigation", { name: "Project workflow" })).toBeInTheDocument();
    expect(screen.getByText("Import the first technical source")).toBeInTheDocument();
  });

  it("restores project and stage context from a deep link", async () => {
    globalThis.history.replaceState({}, "", `/projects/${projectId}/workbench/sources`);
    mockPlatform({ withProject: true });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Documentation Platform" })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "OpenAPI source registry" })).toBeInTheDocument();
    });
    expect(
      screen.getByRole("button", { name: /Current project: Documentation Platform/ }),
    ).toHaveAttribute("title", "Documentation Platform");
    expect(screen.queryByLabelText("Project")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Sources Technical intake/ })).toHaveAttribute(
      "aria-current",
      "step",
    );
  });

  it("responds to browser history events", async () => {
    mockPlatform();

    render(<App />);
    globalThis.history.pushState({}, "", "/system");
    globalThis.dispatchEvent(new PopStateEvent("popstate"));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "System status" })).toBeInTheDocument();
    });
    expect(screen.getByText("Documentation policy")).toBeInTheDocument();
  });

  it("shows an actionable route-not-found state", () => {
    globalThis.history.replaceState({}, "", "/unknown");
    mockPlatform();

    render(<App />);

    expect(screen.getByRole("heading", { name: "Page not found" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Return home" }));
    expect(globalThis.location.pathname).toBe("/");
  });
});
