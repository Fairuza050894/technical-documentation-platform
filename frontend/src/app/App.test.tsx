import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

function getRequestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }
  return input instanceof URL ? input.href : input.url;
}

function mockEmptyPlatform(): void {
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
    return Promise.resolve(
      new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
    );
  });
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("App", () => {
  it("opens the operational overview by default", async () => {
    mockEmptyPlatform();

    render(<App />);

    expect(screen.getByRole("heading", { name: "Overview" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Overview" }).querySelector("svg"),
    ).not.toBeNull();
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /Active projects: 0/ }),
      ).toBeInTheDocument();
    });
    expect(screen.getByText("No active projects")).toBeInTheDocument();
  });

  it("opens the project registry from grouped navigation", async () => {
    mockEmptyPlatform();

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Projects" }));

    expect(screen.getByRole("heading", { name: "Projects" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("No projects yet")).toBeInTheDocument());
  });

  it("opens the source registry from primary navigation", async () => {
    mockEmptyPlatform();

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Source registry" }));

    expect(screen.getByRole("heading", { level: 1, name: "Sources" })).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText("Create a project first")).toBeInTheDocument(),
    );
  });

  it("opens the API catalog from primary navigation", async () => {
    mockEmptyPlatform();

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "API catalog" }));

    expect(screen.getByRole("heading", { name: "API Catalog" })).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText("Create a project first")).toBeInTheDocument(),
    );
  });

  it("opens the Documents workspace from primary navigation", async () => {
    mockEmptyPlatform();

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Documents" }));

    expect(screen.getByRole("heading", { name: "Documents" })).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText("Create a project first")).toBeInTheDocument(),
    );
  });

  it("navigates from an overview quick action", async () => {
    mockEmptyPlatform();

    render(<App />);
    await waitFor(() => expect(screen.getByText("Quick actions")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /Import OpenAPI/ }));

    expect(screen.getByRole("heading", { level: 1, name: "Sources" })).toBeInTheDocument();
  });

  it("shows backend metadata under System status", async () => {
    mockEmptyPlatform();

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "System status" }));

    await waitFor(() => {
      expect(screen.getByText("0.1.0")).toBeInTheDocument();
      expect(screen.getAllByText("development").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("Documentation policy")).toBeInTheDocument();
  });
});
