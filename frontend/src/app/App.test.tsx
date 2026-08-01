import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

const workspaceId = "00000000-0000-4000-8000-000000000001";
const secondWorkspaceId = "22222222-2222-4222-8222-222222222222";
const projectId = "11111111-1111-4111-8111-111111111111";
const featureId = "33333333-3333-4333-8333-333333333333";

function getRequestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }
  return input instanceof URL ? input.href : input.url;
}

function workspaceRecord(id = workspaceId, key = "GENERAL", name = "General Workspace") {
  return {
    id,
    key,
    name,
    description: "Workspace documentation boundary",
    status: "ACTIVE",
    created_at: "2026-07-29T00:00:00Z",
    updated_at: "2026-07-30T00:00:00Z",
  };
}

function projectRecord() {
  return {
    id: projectId,
    key: "DOCS",
    name: "Documentation Platform",
    description: "Source-backed documentation",
    workspace_id: workspaceId,
    ownership_type: "TEAM",
    workspace_type: "ENTERPRISE",
    status: "ACTIVE",
    created_at: "2026-07-29T00:00:00Z",
    updated_at: "2026-07-30T00:00:00Z",
  };
}


function featureRecord() {
  return {
    id: featureId,
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

function mockPlatform({
  withProject = false,
  withSecondWorkspace = false,
  withFeature = false,
}: {
  withProject?: boolean;
  withSecondWorkspace?: boolean;
  withFeature?: boolean;
} = {}): void {
  vi.spyOn(globalThis, "fetch").mockImplementation((input: RequestInfo | URL) => {
    const url = getRequestUrl(input);
    if (url.endsWith("/api/identity/me")) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            subject_id: "local-technical-writer",
            display_name: "Technical Writer",
            email: "technical.writer@local.invalid",
            provider: "local",
            assurance: "DEVELOPMENT",
            audit_actor: "Technical Writer [local:local-technical-writer]",
          }),
          { status: 200 },
        ),
      );
    }
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
    if (url.endsWith("/api/workspaces")) {
      const items = [
        workspaceRecord(),
        ...(withSecondWorkspace
          ? [workspaceRecord(secondWorkspaceId, "ERP", "ERP Workspace")]
          : []),
      ];
      return Promise.resolve(
        new Response(JSON.stringify({ items, total: items.length }), { status: 200 }),
      );
    }
    if (url.endsWith(`/api/workspaces/${workspaceId}/projects`)) {
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
    if (url.endsWith(`/api/workspaces/${secondWorkspaceId}/projects`)) {
      return Promise.resolve(
        new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
      );
    }
    if (url.endsWith(`/api/projects/${projectId}`)) {
      return Promise.resolve(new Response(JSON.stringify(projectRecord()), { status: 200 }));
    }
    if (url.endsWith(`/api/workspaces/${workspaceId}/projects/${projectId}/features`)) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            items: withFeature ? [featureRecord()] : [],
            total: withFeature ? 1 : 0,
          }),
          { status: 200 },
        ),
      );
    }
    if (url.endsWith(`/api/workspaces/${workspaceId}/projects/${projectId}/features/${featureId}/documentation-map`)) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            feature_id: featureId,
            policy_key: "feature-documentation-baseline-v1",
            total: 8,
            items: [
              {
                document_type: "SYSTEM_REQUIREMENTS_SPECIFICATION",
                requirement: "REQUIRED",
                coverage_status: "MISSING",
                document_id: null,
                policy_key: "feature-documentation-baseline-v1",
                created_at: "2026-08-01T00:00:00Z",
                updated_at: "2026-08-01T00:00:00Z",
              },
            ],
          }),
          { status: 200 },
        ),
      );
    }
    if (url.endsWith(`/api/projects/${projectId}/sources`)) {
      return Promise.resolve(
        new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
      );
    }
    if (url.endsWith(`/api/projects/${projectId}/documents`)) {
      return Promise.resolve(
        new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
      );
    }
    return Promise.resolve(
      new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
    );
  });
}

beforeEach(() => {
  globalThis.localStorage.clear();
  globalThis.history.replaceState({}, "", "/");
});

afterEach(() => {
  vi.restoreAllMocks();
  globalThis.localStorage.clear();
  globalThis.history.replaceState({}, "", "/");
});

describe("App", () => {
  it("selects the default workspace before opening Home", async () => {
    mockPlatform();

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Overview" })).toBeInTheDocument();
      expect(globalThis.location.pathname).toBe(`/workspaces/${workspaceId}`);
    });
    expect(
      screen.getByRole("button", {
        name: "Switch workspace. Current workspace: GENERAL — General Workspace",
      }),
    ).toHaveAttribute("aria-expanded", "false");
    expect(screen.getByRole("button", { name: "Home" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.queryByRole("button", { name: "Source registry" })).not.toBeInTheDocument();
    expect(
      await screen.findByRole("button", { name: /Active projects: 0/ }),
    ).toBeInTheDocument();
  });

  it("uses a workspace-scoped URL for the project registry", async () => {
    mockPlatform();

    render(<App />);
    await screen.findByRole("heading", { name: "Overview" });
    fireEvent.click(screen.getByRole("button", { name: "Projects" }));

    expect(globalThis.location.pathname).toBe(`/workspaces/${workspaceId}/projects`);
    expect(screen.getByRole("heading", { name: "Projects" })).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText("No projects in this workspace")).toBeInTheDocument(),
    );
  });

  it("opens a project workbench without replacing the workspace selector", async () => {
    mockPlatform({ withProject: true });

    render(<App />);
    await screen.findByRole("heading", { name: "Overview" });
    fireEvent.click(screen.getByRole("button", { name: "Projects" }));
    await waitFor(() =>
      expect(screen.getByText("Documentation Platform")).toBeInTheDocument(),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Open Documentation Platform workbench" }),
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Documentation Platform" }),
      ).toBeInTheDocument();
    });
    expect(globalThis.location.pathname).toBe(
      `/workspaces/${workspaceId}/projects/${projectId}/workbench/overview`,
    );
    expect(
      screen.getByRole("button", {
        name: "Switch workspace. Current workspace: GENERAL — General Workspace",
      }),
    ).toHaveAttribute("aria-expanded", "false");
    expect(screen.getByRole("navigation", { name: "Project workflow" })).toBeInTheDocument();
    expect(screen.getByText("Define the first feature or module")).toBeInTheDocument();
  });

  it("restores workspace, project, and stage context from a deep link", async () => {
    globalThis.history.replaceState(
      {},
      "",
      `/workspaces/${workspaceId}/projects/${projectId}/workbench/sources`,
    );
    mockPlatform({ withProject: true });

    render(<App />);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Documentation Platform" }),
      ).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "OpenAPI source registry" })).toBeInTheDocument();
    });
    expect(
      screen.getByRole("button", {
        name: "Switch workspace. Current workspace: GENERAL — General Workspace",
      }),
    ).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByLabelText("Project")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Sources Technical intake/ })).toHaveAttribute(
      "aria-current",
      "step",
    );
  });

  it("restores a feature documentation map from a deep link", async () => {
    globalThis.history.replaceState(
      {},
      "",
      `/workspaces/${workspaceId}/projects/${projectId}/workbench/features/${featureId}`,
    );
    mockPlatform({ withProject: true, withFeature: true });

    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "Documentation Core" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Features Capability map/ }),
    ).toHaveAttribute("aria-current", "step");
    expect(
      await screen.findByText("System requirements specification"),
    ).toBeInTheDocument();
  });

  it("upgrades a legacy project deep link to its workspace-scoped route", async () => {
    globalThis.history.replaceState({}, "", `/projects/${projectId}/workbench/sources`);
    mockPlatform({ withProject: true });

    render(<App />);

    await waitFor(() => {
      expect(globalThis.location.pathname).toBe(
        `/workspaces/${workspaceId}/projects/${projectId}/workbench/sources`,
      );
    });
  });

  it("switches workspace context and returns to that workspace home", async () => {
    mockPlatform({ withSecondWorkspace: true });

    render(<App />);
    await screen.findByRole("heading", { name: "Overview" });
    fireEvent.click(
      screen.getByRole("button", {
        name: "Switch workspace. Current workspace: GENERAL — General Workspace",
      }),
    );
    fireEvent.click(
      screen.getByRole("menuitemradio", { name: "ERP — ERP Workspace" }),
    );

    await waitFor(() => {
      expect(globalThis.location.pathname).toBe(`/workspaces/${secondWorkspaceId}`);
    });
    expect(globalThis.localStorage.getItem("tdp.last-workspace-id")).toBe(secondWorkspaceId);
  });

  it("responds to browser history events", async () => {
    mockPlatform();

    render(<App />);
    await screen.findByRole("heading", { name: "Overview" });
    globalThis.history.pushState({}, "", "/system");
    globalThis.dispatchEvent(new PopStateEvent("popstate"));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "System status" })).toBeInTheDocument();
    });
    expect(screen.getByText("Documentation policy")).toBeInTheDocument();
  });

  it("shows an actionable route-not-found state", async () => {
    globalThis.history.replaceState({}, "", "/unknown");
    mockPlatform();

    render(<App />);

    expect(await screen.findByRole("heading", { name: "Page not found" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Return home" }));
    expect(globalThis.location.pathname).toBe(`/workspaces/${workspaceId}`);
  });
});
