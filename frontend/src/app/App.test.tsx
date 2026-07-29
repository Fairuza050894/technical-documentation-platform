import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

function getRequestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }
  return input instanceof URL ? input.href : input.url;
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("App", () => {
  it("opens the project registry as the current vertical slice", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
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

    render(<App />);

    expect(screen.getByRole("heading", { name: "Projects" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("No projects yet")).toBeInTheDocument());
  });

  it("opens the source registry from primary navigation", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
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

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Sources" }));

    expect(screen.getByRole("heading", { name: "Sources" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Create a project first")).toBeInTheDocument());
  });

  it("opens the API catalog from primary navigation", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
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

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "API Catalog" }));

    expect(screen.getByRole("heading", { name: "API Catalog" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Create a project first")).toBeInTheDocument());
  });

  it("opens the Documents workspace from primary navigation", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
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

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Documents" }));

    expect(screen.getByRole("heading", { name: "Documents" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Create a project first")).toBeInTheDocument());
  });

  it("shows backend metadata on the overview", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
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

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Overview" }));

    await waitFor(() => {
      expect(screen.getByText("Version 0.1.0 · development")).toBeInTheDocument();
    });
  });
});
