import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SourceWorkspace } from "./SourceWorkspace";

function getRequestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }
  return input instanceof URL ? input.href : input.url;
}

const project = {
  id: "5e742f10-bdc0-4a24-b6dd-3002e875cc85",
  key: "DOCS",
  name: "Documentation Platform",
  description: "",
  workspace_type: "PERSONAL",
  status: "ACTIVE",
  created_at: "2026-07-29T00:00:00+00:00",
  updated_at: "2026-07-29T00:00:00+00:00",
};

const source = {
  id: "7f6c4647-050b-430d-a46e-391f7d7ad25e",
  project_id: project.id,
  name: "Commerce OpenAPI",
  source_type: "OPENAPI_FILE",
  status: "READY",
  original_file_name: "commerce.yaml",
  media_type: "YAML",
  checksum: "a".repeat(64),
  openapi_version: "3.1.0",
  api_title: "Commerce API",
  api_version: "1.0.0",
  path_count: 1,
  operation_count: 2,
  created_at: "2026-07-29T00:00:00+00:00",
  updated_at: "2026-07-29T00:00:00+00:00",
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe("SourceWorkspace", () => {
  it("imports an OpenAPI file and adds it to the registry", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = getRequestUrl(input);
      if (url.endsWith("/api/projects")) {
        return Promise.resolve(
          new Response(JSON.stringify({ items: [project], total: 1 }), { status: 200 }),
        );
      }
      if (url.endsWith(`/api/projects/${project.id}/sources/openapi`) && init?.method === "POST") {
        expect(init.body).toBeInstanceOf(FormData);
        return Promise.resolve(new Response(JSON.stringify(source), { status: 201 }));
      }
      return Promise.resolve(
        new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
      );
    });

    render(<SourceWorkspace />);
    await waitFor(() => expect(screen.getByText("No sources for this project")).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText("Source name"), {
      target: { value: "Commerce OpenAPI" },
    });
    const file = new File(["openapi: 3.1.0"], "commerce.yaml", {
      type: "application/yaml",
    });
    fireEvent.change(screen.getByLabelText("OpenAPI file"), {
      target: { files: [file] },
    });
    const submitButton = screen.getByRole("button", { name: "Import source" });
    const form = submitButton.closest("form");
    expect(form).not.toBeNull();
    fireEvent.submit(form as HTMLFormElement);

    await waitFor(() => {
      expect(screen.getByText("Commerce OpenAPI")).toBeInTheDocument();
      expect(screen.getByText("2 operations")).toBeInTheDocument();
    });
  });

  it("explains that a project must exist first", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
    );

    render(<SourceWorkspace />);

    await waitFor(() => {
      expect(screen.getByText("Create a project first")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Import source" })).toBeDisabled();
    });
  });
});
