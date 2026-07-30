import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { OperationalOverview } from "./OperationalOverview";

function getRequestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }
  return input instanceof URL ? input.href : input.url;
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("OperationalOverview", () => {
  it("builds source-backed metrics, attention, activity, and project health", async () => {
    const onNavigate = vi.fn();

    vi.spyOn(globalThis, "fetch").mockImplementation((input: RequestInfo | URL) => {
      const url = getRequestUrl(input);

      if (url.endsWith("/api/projects")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: "project-1",
                  key: "COMM",
                  name: "Commerce API",
                  description: "",
                  workspace_type: "PERSONAL",
                  status: "ACTIVE",
                  created_at: "2026-07-29T08:00:00Z",
                  updated_at: "2026-07-29T08:00:00Z",
                },
              ],
              total: 1,
            }),
          ),
        );
      }

      if (url.endsWith("/api/projects/project-1/sources")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: "source-1",
                  project_id: "project-1",
                  name: "Commerce OpenAPI",
                  source_type: "OPENAPI_FILE",
                  status: "READY",
                  original_file_name: "commerce.yaml",
                  media_type: "YAML",
                  checksum: "source-checksum",
                  openapi_version: "3.1.0",
                  api_title: "Commerce API",
                  api_version: "2.0.0",
                  path_count: 4,
                  operation_count: 5,
                  created_at: "2026-07-29T08:10:00Z",
                  updated_at: "2026-07-29T08:10:00Z",
                },
              ],
              total: 1,
            }),
          ),
        );
      }

      if (url.endsWith("/api/sources/source-1/synchronizations")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: "sync-completed",
                  project_id: "project-1",
                  source_id: "source-1",
                  source_checksum: "source-checksum",
                  status: "COMPLETED",
                  operation_count: 5,
                  schema_count: 3,
                  error_code: "",
                  error_message: "",
                  started_at: "2026-07-29T08:20:00Z",
                  completed_at: "2026-07-29T08:21:00Z",
                },
                {
                  id: "sync-failed",
                  project_id: "project-1",
                  source_id: "source-1",
                  source_checksum: "source-checksum",
                  status: "FAILED",
                  operation_count: 0,
                  schema_count: 0,
                  error_code: "SYNCHRONIZATION_FAILED",
                  error_message: "Invalid reference",
                  started_at: "2026-07-29T09:20:00Z",
                  completed_at: "2026-07-29T09:21:00Z",
                },
              ],
              total: 2,
            }),
          ),
        );
      }

      if (url.endsWith("/api/projects/project-1/documents")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: "version-2",
                  document_id: "document-1",
                  project_id: "project-1",
                  source_id: "source-1",
                  target_run_id: "sync-completed",
                  baseline_run_id: null,
                  document_type: "TECHNICAL_SOURCE_OVERVIEW",
                  document_format: "MARKDOWN",
                  version: "1.1",
                  status: "IN_REVIEW",
                  title: "Technical Source Overview — Commerce API",
                  file_name: "commerce-api.md",
                  checksum: "document-checksum",
                  operation_count: 5,
                  schema_count: 3,
                  breaking_change_count: 2,
                  revision_reason: "Review breaking changes.",
                  created_by: "Technical Writer",
                  generated_at: "2026-07-29T10:00:00Z",
                  updated_at: "2026-07-29T10:05:00Z",
                  submitted_at: "2026-07-29T10:05:00Z",
                  approved_at: null,
                  superseded_at: null,
                },
              ],
              total: 1,
            }),
          ),
        );
      }

      throw new Error(`Unexpected request: ${url}`);
    });

    render(
      <OperationalOverview
        serviceState="available"
        serviceVersion="0.1.0"
        onNavigate={onNavigate}
      />,
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Active projects: 1/ })).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: /Ready sources: 1/ })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Completed snapshots: 1/ }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Pending reviews: 1/ })).toBeInTheDocument();
    expect(screen.getByText("Failed synchronizations")).toBeInTheDocument();
    expect(
      screen.getByText("Breaking findings in current document versions"),
    ).toBeInTheDocument();
    expect(screen.getByText("3 conditions")).toBeInTheDocument();
    expect(screen.getByText("Document v1.1")).toBeInTheDocument();
    expect(
      screen.getByRole("list", {
        name: "Recent synchronization and document activities",
      }),
    ).toBeInTheDocument();
    expect(document.querySelector(".signal-strip")).not.toBeNull();
    expect(document.querySelector(".metric-card")).toBeNull();

    const projectHealth = screen.getByRole("table", {
      name: "Active project operational health",
    });
    expect(within(projectHealth).getByText("Commerce API")).toBeInTheDocument();
    expect(within(projectHealth).getByText("5")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Pending reviews: 1/ }));
    expect(onNavigate).toHaveBeenCalledWith("Documents", "project-1");
  });

  it("shows a clear state when no operational issues exist", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input: RequestInfo | URL) => {
      const url = getRequestUrl(input);
      if (url.endsWith("/api/projects")) {
        return Promise.resolve(
          new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
        );
      }
      throw new Error(`Unexpected request: ${url}`);
    });

    render(
      <OperationalOverview
        serviceState="available"
        serviceVersion="0.1.0"
        onNavigate={vi.fn()}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("No operational issues detected")).toBeInTheDocument();
    });
    expect(screen.getByText("No active projects")).toBeInTheDocument();
  });
});
