import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ProjectWorkbench } from "./ProjectWorkbench";

const workspaceId = "00000000-0000-4000-8000-000000000001";
const projectId = "11111111-1111-4111-8111-111111111111";

function getRequestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }
  return input instanceof URL ? input.href : input.url;
}

function projectRecord(
  overrideWorkspaceId = workspaceId,
  status: "ACTIVE" | "ARCHIVED" = "ACTIVE",
) {
  return {
    id: projectId,
    key: "DOCS",
    name: "Documentation Platform",
    description: "Source-backed documentation",
    workspace_id: overrideWorkspaceId,
    ownership_type: "TEAM",
    workspace_type: "ENTERPRISE",
    status,
    created_at: "2026-07-29T00:00:00Z",
    updated_at: "2026-07-30T00:00:00Z",
  };
}

function featureRecord() {
  return {
    id: "33333333-3333-4333-8333-333333333333",
    project_id: projectId,
    key: "DOCS-CORE",
    name: "Documentation Core",
    description: "Core documentation capability",
    kind: "MODULE",
    owner: "Platform Team",
    status: "ACTIVE",
    documentation_coverage: {
      required_total: 5,
      available_required: 0,
      missing_required: 5,
      optional_total: 3,
    },
    created_at: "2026-08-01T00:00:00Z",
    updated_at: "2026-08-01T00:00:00Z",
  };
}

function readinessRecord() {
  return {
    project_id: projectId,
    project_status: "ACTIVE",
    policy_version: "document-readiness-v1",
    total: 1,
    ready_total: 0,
    partially_ready_total: 0,
    not_ready_total: 1,
    eligible_total: 0,
    required_total: 1,
    required_not_ready_total: 1,
    items: [
      {
        project_id: projectId,
        policy_version: "document-readiness-v1",
        document_type: "LLD",
        display_name: "Low Level Design",
        automation_profile: "EVIDENCE_DRIVEN",
        requirement: "REQUIRED",
        availability: "MISSING",
        latest_status: null,
        readiness_state: "NOT_READY",
        eligible: false,
        findings: [
          {
            rule_code: "LLD_NORMALIZED_TECHNICAL_EVIDENCE_REQUIRED",
            document_type: "LLD",
            severity: "BLOCKER",
            message: "Low Level Design requires normalized technical evidence.",
            missing_input: "evidence-kind:CATALOG_SNAPSHOT",
            remediation: "Register a completed normalized API Catalog snapshot as evidence.",
            supporting_references: [],
          },
        ],
        evidence_count: 1,
        observed_claim_count: 0,
        inferred_claim_count: 0,
        unverified_claim_count: 0,
      },
    ],
  };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ProjectWorkbench", () => {
  it("derives the next action from project evidence", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = getRequestUrl(input);
      if (url.endsWith(`/api/projects/${projectId}`)) {
        return Promise.resolve(
          new Response(JSON.stringify(projectRecord()), { status: 200 }),
        );
      }
      if (url.endsWith(`/api/workspaces/${workspaceId}/projects/${projectId}/features`)) {
        return Promise.resolve(
          new Response(JSON.stringify({ items: [featureRecord()], total: 1 }), { status: 200 }),
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
      );
    });
    const navigateStage = vi.fn();

    render(
      <ProjectWorkbench
        workspaceId={workspaceId}
        projectId={projectId}
        stage="overview"
        featureId={null}
        onNavigateStage={navigateStage}
        onNavigateFeature={vi.fn()}
        onBackToProjects={vi.fn()}
        onProjectResolved={vi.fn()}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Import the first technical source")).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: "Projects" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Open source intake" }));
    expect(navigateStage).toHaveBeenCalledWith("sources");
  });

  it("integrates backend document readiness without duplicating policy in the UI", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = getRequestUrl(input);
      if (url.endsWith(`/api/projects/${projectId}`)) {
        return Promise.resolve(
          new Response(JSON.stringify(projectRecord()), { status: 200 }),
        );
      }
      if (url.endsWith(`/api/workspaces/${workspaceId}/projects/${projectId}/features`)) {
        return Promise.resolve(
          new Response(JSON.stringify({ items: [featureRecord()], total: 1 }), { status: 200 }),
        );
      }
      if (url.endsWith(`/api/projects/${projectId}/sources`)) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: "source-1",
                  project_id: projectId,
                  name: "Commerce API",
                  status: "READY",
                },
              ],
              total: 1,
            }),
            { status: 200 },
          ),
        );
      }
      if (url.endsWith("/api/sources/source-1/synchronizations")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: "sync-1",
                  source_id: "source-1",
                  project_id: projectId,
                  status: "COMPLETED",
                },
              ],
              total: 1,
            }),
            { status: 200 },
          ),
        );
      }
      if (url.endsWith(`/api/projects/${projectId}/readiness`)) {
        return Promise.resolve(new Response(JSON.stringify(readinessRecord()), { status: 200 }));
      }
      if (url.endsWith(`/api/projects/${projectId}/documentation-checklist`)) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              project_id: projectId,
              policy_key: "project-documentation-baseline-v1",
              registry_schema_version: "document-type-registry-v1",
              items: [],
              total: 0,
              required_total: 0,
              supplementary_total: 0,
              available_total: 0,
              missing_required_total: 0,
            }),
            { status: 200 },
          ),
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
      );
    });
    const navigateStage = vi.fn();

    render(
      <ProjectWorkbench
        workspaceId={workspaceId}
        projectId={projectId}
        stage="overview"
        featureId={null}
        onNavigateStage={navigateStage}
        onNavigateFeature={vi.fn()}
        onBackToProjects={vi.fn()}
        onProjectResolved={vi.fn()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Project documentation" }),
    ).toBeInTheDocument();
    expect(await screen.findByText("Low Level Design")).toBeInTheDocument();
    expect(screen.getAllByText("Blocked").length).toBeGreaterThan(0);
    expect(await screen.findByText("Complete evidence for Low Level Design")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Open API catalog" }));
    expect(navigateStage).toHaveBeenCalledWith("catalog");
  });

  it("recommends defining a capability before technical intake", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = getRequestUrl(input);
      if (url.endsWith(`/api/projects/${projectId}`)) {
        return Promise.resolve(
          new Response(JSON.stringify(projectRecord()), { status: 200 }),
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
      );
    });
    const navigateStage = vi.fn();

    render(
      <ProjectWorkbench
        workspaceId={workspaceId}
        projectId={projectId}
        stage="overview"
        featureId={null}
        onNavigateStage={navigateStage}
        onNavigateFeature={vi.fn()}
        onBackToProjects={vi.fn()}
        onProjectResolved={vi.fn()}
      />,
    );

    expect(
      await screen.findByText("Define the first feature or module"),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Open capability registry" }));
    expect(navigateStage).toHaveBeenCalledWith("features");
  });

  it("keeps archived project evidence available in a read-only workbench", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = getRequestUrl(input);
      if (url.endsWith(`/api/projects/${projectId}`)) {
        return Promise.resolve(
          new Response(JSON.stringify(projectRecord(workspaceId, "ARCHIVED")), { status: 200 }),
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
      );
    });
    const navigateStage = vi.fn();
    const onProjectResolved = vi.fn();

    render(
      <ProjectWorkbench
        workspaceId={workspaceId}
        projectId={projectId}
        stage="overview"
        featureId={null}
        onNavigateStage={navigateStage}
        onNavigateFeature={vi.fn()}
        onBackToProjects={vi.fn()}
        onProjectResolved={onProjectResolved}
      />,
    );

    const readOnlyStatus = await screen.findByRole("status", {
      name: "Archived project read-only status",
    });
    expect(readOnlyStatus).toHaveTextContent("Existing evidence remains available in read-only mode");
    expect(readOnlyStatus).toHaveTextContent("New intake and lifecycle changes are blocked");
    expect(onProjectResolved).toHaveBeenCalledWith(projectRecord(workspaceId, "ARCHIVED"));

    const sourceStage = screen.getByRole("button", { name: /Sources/ });
    expect(sourceStage).toBeEnabled();
    fireEvent.click(sourceStage);
    expect(navigateStage).toHaveBeenCalledWith("sources");
  });

  it("rejects a project that belongs to another workspace", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = getRequestUrl(input);
      if (url.endsWith(`/api/projects/${projectId}`)) {
        return Promise.resolve(
          new Response(
            JSON.stringify(projectRecord("22222222-2222-4222-8222-222222222222")),
            { status: 200 },
          ),
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
      );
    });

    render(
      <ProjectWorkbench
        workspaceId={workspaceId}
        projectId={projectId}
        stage="overview"
        featureId={null}
        onNavigateStage={vi.fn()}
        onNavigateFeature={vi.fn()}
        onBackToProjects={vi.fn()}
        onProjectResolved={vi.fn()}
      />,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Project not found" })).toBeInTheDocument();
    });
  });

  it("shows an actionable missing-project state", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: "PROJECT_NOT_FOUND",
            message: "Project missing was not found.",
          },
        }),
        { status: 404 },
      ),
    );
    const back = vi.fn();

    render(
      <ProjectWorkbench
        workspaceId={workspaceId}
        projectId="missing"
        stage="overview"
        featureId={null}
        onNavigateStage={vi.fn()}
        onNavigateFeature={vi.fn()}
        onBackToProjects={back}
        onProjectResolved={vi.fn()}
      />,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Project not found" })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: "Open project registry" }));
    expect(back).toHaveBeenCalledOnce();
  });
});
