import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("App", () => {
  it("opens the project registry as the current vertical slice", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/api/health")) {
        return new Response(
          JSON.stringify({
            status: "ok",
            service: "Technical Documentation Platform",
            version: "0.1.0",
            environment: "development",
          }),
          { status: 200 },
        );
      }
      return new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 });
    });

    render(<App />);

    expect(screen.getByRole("heading", { name: "Projects" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("No projects yet")).toBeInTheDocument());
  });

  it("shows backend metadata on the overview", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/api/health")) {
        return new Response(
          JSON.stringify({
            status: "ok",
            service: "Technical Documentation Platform",
            version: "0.1.0",
            environment: "development",
          }),
          { status: 200 },
        );
      }
      return new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 });
    });

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Overview" }));

    await waitFor(() => {
      expect(screen.getByText("Version 0.1.0 · development")).toBeInTheDocument();
    });
  });
});
