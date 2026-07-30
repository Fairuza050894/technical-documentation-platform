import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { GeneratedDocumentSummary } from "./types";
import { DocumentsWorkspace } from "./DocumentsWorkspace";

const projectId = "11111111-1111-4111-8111-111111111111";
const documentId = "22222222-2222-4222-8222-222222222222";
const versionOneId = "33333333-3333-4333-8333-333333333333";
const versionTwoId = "44444444-4444-4444-8444-444444444444";
const runOneId = "55555555-5555-4555-8555-555555555555";
const runTwoId = "66666666-6666-4666-8666-666666666666";

function documentVersion(
  id: string,
  version: string,
  status: GeneratedDocumentSummary["status"],
  targetRunId: string,
): GeneratedDocumentSummary {
  return {
    id,
    document_id: documentId,
    project_id: projectId,
    source_id: `source-${version}`,
    target_run_id: targetRunId,
    baseline_run_id: version === "1.0" ? null : runOneId,
    document_type: "TECHNICAL_SOURCE_OVERVIEW",
    document_format: "MARKDOWN",
    version,
    status,
    title: "Technical Source Overview — Commerce API",
    file_name: `commerce-api-v${version}.md`,
    checksum: version === "1.0" ? "a".repeat(64) : "b".repeat(64),
    operation_count: version === "1.0" ? 2 : 3,
    schema_count: 2,
    breaking_change_count: version === "1.0" ? 0 : 1,
    revision_reason: version === "1.0" ? "Initial baseline." : "Add validation endpoint.",
    created_by: "Technical Writer",
    generated_at: version === "1.0" ? "2026-07-28T00:00:00Z" : "2026-07-29T00:00:00Z",
    updated_at: "2026-07-29T00:00:00Z",
    submitted_at: status === "DRAFT" ? null : "2026-07-29T01:00:00Z",
    approved_at: status === "APPROVED" ? "2026-07-29T02:00:00Z" : null,
    superseded_at: null,
  };
}

function requestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }
  return input instanceof URL ? input.href : input.url;
}

function commonResponse(url: string, versions: GeneratedDocumentSummary[]): Response | null {
  if (url.endsWith("/api/projects")) {
    return new Response(
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
    );
  }
  if (url.endsWith(`/api/projects/${projectId}/sources`)) {
    return new Response(
      JSON.stringify({
        items: [
          { id: "source-v1", project_id: projectId, name: "Commerce v1", status: "READY" },
          { id: "source-v2", project_id: projectId, name: "Commerce v2", status: "READY" },
        ],
        total: 2,
      }),
    );
  }
  if (url.endsWith("/api/sources/source-v1/synchronizations")) {
    return new Response(
      JSON.stringify({
        items: [{ id: runOneId, status: "COMPLETED", started_at: "2026-07-28T00:00:00Z" }],
        total: 1,
      }),
    );
  }
  if (url.endsWith("/api/sources/source-v2/synchronizations")) {
    return new Response(
      JSON.stringify({
        items: [{ id: runTwoId, status: "COMPLETED", started_at: "2026-07-29T00:00:00Z" }],
        total: 1,
      }),
    );
  }
  if (url.endsWith(`/api/projects/${projectId}/documents`)) {
    return new Response(JSON.stringify({ items: versions, total: versions.length }));
  }
  return null;
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("DocumentsWorkspace", () => {
  it("shows version history and submits a draft for review", async () => {
    let draft = documentVersion(versionTwoId, "1.1", "DRAFT", runTwoId);
    const approved = documentVersion(versionOneId, "1.0", "APPROVED", runOneId);

    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = requestUrl(input);
      const common = commonResponse(url, [draft, approved]);
      if (common !== null) {
        return Promise.resolve(common);
      }
      if (url.endsWith(`/api/document-versions/${versionTwoId}`)) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...draft,
              content: "# Technical Source Overview: Commerce API\n",
              reused_existing_version: false,
            }),
          ),
        );
      }
      if (url.endsWith(`/api/document-versions/${versionTwoId}/workflow-events`)) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: "event-generated",
                  version_id: versionTwoId,
                  actor: "Technical Writer",
                  action: "GENERATED",
                  previous_status: null,
                  new_status: "DRAFT",
                  comment: "Add validation endpoint.",
                  created_at: "2026-07-29T00:00:00Z",
                },
              ],
              total: 1,
            }),
          ),
        );
      }
      if (
        url.endsWith(`/api/document-versions/${versionTwoId}/submit-review`) &&
        init?.method === "POST"
      ) {
        draft = { ...draft, status: "IN_REVIEW", submitted_at: "2026-07-29T01:00:00Z" };
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...draft,
              content: "# Technical Source Overview: Commerce API\n",
              reused_existing_version: false,
            }),
          ),
        );
      }
      return Promise.resolve(new Response(JSON.stringify({ items: [], total: 0 })));
    });

    render(<DocumentsWorkspace />);

    await waitFor(() => expect(screen.getByText("v1.1")).toBeInTheDocument());
    const openButton = screen.getAllByRole("button", { name: "Open" })[0];
    if (openButton === undefined) {
      throw new Error("Expected at least one Open button.");
    }
    fireEvent.click(openButton);

    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Submit for review" })).toBeEnabled(),
    );
    expect(screen.getByText("Workflow timeline")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Submit for review" }));

    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent("Version 1.1 is now In Review."),
    );
  });

  it("uses a neutral label when a replaced version has no known successor", async () => {
    const previous = documentVersion(versionOneId, "1.0", "SUPERSEDED", runOneId);

    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const common = commonResponse(requestUrl(input), [previous]);
      return Promise.resolve(
        common ?? new Response(JSON.stringify({ items: [], total: 0 })),
      );
    });

    render(<DocumentsWorkspace />);

    await waitFor(() =>
      expect(
        screen.getByText("Previous version", { selector: ".status-badge" }),
      ).toBeInTheDocument(),
    );
    expect(screen.getByText("No longer current")).toBeInTheDocument();
    expect(
      screen.queryByText("Replaced", { selector: ".status-badge" }),
    ).not.toBeInTheDocument();
  });

  it("compares document versions and filters structured section changes", async () => {
    const target = documentVersion(versionTwoId, "1.1", "DRAFT", runTwoId);
    const baseline = documentVersion(versionOneId, "1.0", "SUPERSEDED", runOneId);

    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = requestUrl(input);
      const common = commonResponse(url, [target, baseline]);
      if (common !== null) {
        return Promise.resolve(common);
      }
      if (url.endsWith("/api/document-version-comparisons") && init?.method === "POST") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              baseline_version_id: versionOneId,
              target_version_id: versionTwoId,
              document_id: documentId,
              total: 2,
              added_total: 1,
              modified_total: 1,
              removed_total: 0,
              changes: [
                {
                  section_key: "endpoint-catalog",
                  section_title: "Endpoint catalog",
                  kind: "MODIFIED",
                  before_checksum: "a".repeat(64),
                  after_checksum: "b".repeat(64),
                  before_excerpt: "POST /orders",
                  after_excerpt: "POST /orders and POST /orders/validate",
                },
                {
                  section_key: "release-notes",
                  section_title: "Release notes",
                  kind: "ADDED",
                  before_checksum: "",
                  after_checksum: "c".repeat(64),
                  before_excerpt: "",
                  after_excerpt: "Validation endpoint added.",
                },
              ],
            }),
          ),
        );
      }
      return Promise.resolve(new Response(JSON.stringify({ items: [], total: 0 })));
    });

    render(<DocumentsWorkspace />);

    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Compare versions" })).toBeEnabled(),
    );
    expect(screen.getByText("Replaced", { selector: ".status-badge" })).toBeInTheDocument();
    expect(screen.getByText("Replaced by v1.1")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Compare versions" }));

    await waitFor(() => expect(screen.getByText("Endpoint catalog")).toBeInTheDocument());
    expect(screen.getByText("Release notes")).toBeInTheDocument();
    expect(screen.getByText("2", { selector: ".comparison-summary strong" })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Change filter"), {
      target: { value: "ADDED" },
    });
    expect(screen.queryByText("Endpoint catalog")).not.toBeInTheDocument();
    expect(screen.getByText("Release notes")).toBeInTheDocument();
  });
});
