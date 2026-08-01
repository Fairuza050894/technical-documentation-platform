import { describe, expect, it } from "vitest";

import {
  parseRoute,
  projectStagePath,
  routePath,
  workspaceHomePath,
  workspaceProjectStagePath,
  workspaceProjectsPath,
} from "./router";

const workspaceId = "workspace 1";
const projectId = "project 1";

describe("workspace and project routing", () => {
  it("parses global and workspace routes", () => {
    expect(parseRoute("/")).toEqual({ name: "home", workspaceId: null });
    expect(parseRoute("/projects/")).toEqual({ name: "projects", workspaceId: null });
    expect(parseRoute("/workspaces")).toEqual({ name: "workspaces" });
    expect(parseRoute("/workspaces/workspace-1")).toEqual({
      name: "home",
      workspaceId: "workspace-1",
    });
    expect(parseRoute("/workspaces/workspace-1/projects")).toEqual({
      name: "projects",
      workspaceId: "workspace-1",
    });
    expect(parseRoute("/system")).toEqual({ name: "system" });
  });

  it("parses and builds persistent workspace-scoped project routes", () => {
    const route = parseRoute(
      "/workspaces/workspace-1/projects/project-1/workbench/documents",
    );

    expect(route).toEqual({
      name: "project",
      workspaceId: "workspace-1",
      projectId: "project-1",
      stage: "documents",
    });
    expect(routePath(route)).toBe(
      "/workspaces/workspace-1/projects/project-1/workbench/documents",
    );
    expect(workspaceHomePath(workspaceId)).toBe("/workspaces/workspace%201");
    expect(workspaceProjectsPath(workspaceId)).toBe(
      "/workspaces/workspace%201/projects",
    );
    expect(workspaceProjectStagePath(workspaceId, projectId, "sources")).toBe(
      "/workspaces/workspace%201/projects/project%201/workbench/sources",
    );
  });


  it("parses and builds feature-scoped documentation map routes", () => {
    const route = parseRoute(
      "/workspaces/workspace-1/projects/project-1/workbench/features/feature-1",
    );

    expect(route).toEqual({
      name: "project",
      workspaceId: "workspace-1",
      projectId: "project-1",
      stage: "features",
      featureId: "feature-1",
    });
    expect(
      workspaceProjectStagePath(
        "workspace-1",
        "project-1",
        "features",
        "feature-1",
      ),
    ).toBe(
      "/workspaces/workspace-1/projects/project-1/workbench/features/feature-1",
    );
  });

  it("rejects a feature identifier on a non-feature stage", () => {
    expect(
      parseRoute(
        "/workspaces/workspace-1/projects/project-1/workbench/documents/feature-1",
      ),
    ).toEqual({
      name: "not-found",
      pathname:
        "/workspaces/workspace-1/projects/project-1/workbench/documents/feature-1",
    });
  });

  it("preserves legacy project routes for additive migration", () => {
    expect(parseRoute("/projects/project-1/workbench")).toEqual({
      name: "project",
      workspaceId: null,
      projectId: "project-1",
      stage: "overview",
    });
    expect(projectStagePath(projectId, "sources")).toBe(
      "/projects/project%201/workbench/sources",
    );
  });

  it("falls back to the overview stage when omitted", () => {
    expect(
      parseRoute("/workspaces/workspace-1/projects/project-1/workbench"),
    ).toEqual({
      name: "project",
      workspaceId: "workspace-1",
      projectId: "project-1",
      stage: "overview",
    });
  });

  it("keeps unknown routes explicit", () => {
    expect(
      parseRoute("/workspaces/workspace-1/projects/project-1/workbench/release"),
    ).toEqual({
      name: "not-found",
      pathname: "/workspaces/workspace-1/projects/project-1/workbench/release",
    });
  });
});
