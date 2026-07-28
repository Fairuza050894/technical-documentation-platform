import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("App", () => {
  it("shows the next vertical slice", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("offline"));

    render(<App />);

    expect(screen.getByRole("heading", { name: "Workspace overview" })).toBeInTheDocument();
    expect(screen.getByText("Project and OpenAPI source")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Offline")).toBeInTheDocument());
  });

  it("shows backend metadata when health is available", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
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

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Version 0.1.0 · development")).toBeInTheDocument();
    });
  });
});
