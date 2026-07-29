import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DocumentsWorkspace } from "./DocumentsWorkspace";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("DocumentsWorkspace", () => {
  it("generates and previews a deterministic Technical Source Overview", async () => {
    const projectId = "11111111-1111-4111-8111-111111111111";
    const targetRunId = "22222222-2222-4222-8222-222222222222";
    const documentId = "33333333-3333-4333-8333-333333333333";

    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url =
        typeof input === "string" ? input : input instanceof URL ? input.href : input.url;

      if (url.endsWith("/api/projects")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: projectId,
                  key: "DOCS",
                  name: "Documentation",
                  description: "",
                  workspace_type: "PERSONAL",
                  status: "ACTIVE",
                  created_at: "",
                  updated_at: "",
                },
              ],
              total: 1,
            }),
          ),
        );
      }
      if (url.endsWith(`/api/projects/${projectId}/sources`)) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: "source-v2",
                  project_id: projectId,
                  name: "Commerce v2",
                  status: "READY",
                },
              ],
              total: 1,
            }),
          ),
        );
      }
      if (url.endsWith("/api/sources/source-v2/synchronizations")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: targetRunId,
                  status: "COMPLETED",
                  started_at: "2026-07-29T00:00:00Z",
                },
              ],
              total: 1,
            }),
          ),
        );
      }
      if (
        url.endsWith(`/api/projects/${projectId}/documents/technical-source-overview`) &&
        init?.method === "POST"
      ) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              id: documentId,
              project_id: projectId,
              source_id: "source-v2",
              target_run_id: targetRunId,
              baseline_run_id: null,
              document_type: "TECHNICAL_SOURCE_OVERVIEW",
              document_format: "MARKDOWN",
              title: "Technical Source Overview — Commerce API",
              file_name: "docs-commerce-v2-technical-source-overview.md",
              checksum: "a".repeat(64),
              operation_count: 3,
              schema_count: 2,
              breaking_change_count: 0,
              generated_at: "2026-07-29T00:00:00Z",
              content: "# Technical Source Overview: Commerce API\n",
            }),
          ),
        );
      }
      if (url.endsWith(`/api/projects/${projectId}/documents`)) {
        return Promise.resolve(
          new Response(JSON.stringify({ items: [], total: 0 })),
        );
      }
      return Promise.resolve(new Response(JSON.stringify({ items: [], total: 0 })));
    });

    render(<DocumentsWorkspace />);

    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Generate overview" })).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Generate overview" }));

    await waitFor(() =>
      expect(
        screen.getByRole("heading", {
          name: "Technical Source Overview — Commerce API",
        }),
      ).toBeInTheDocument(),
    );
    expect(
      screen.getByText("# Technical Source Overview: Commerce API"),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Download Markdown" })).toHaveAttribute(
      "href",
      `http://127.0.0.1:8000/api/documents/${documentId}/download`,
    );
  });
});
