import { describe, expect, it } from "vitest";

import { parseRoute, projectStagePath, routePath } from "./router";

describe("project workbench routing", () => {
  it("parses global routes", () => {
    expect(parseRoute("/")).toEqual({ name: "home" });
    expect(parseRoute("/projects/")).toEqual({ name: "projects" });
    expect(parseRoute("/system")).toEqual({ name: "system" });
  });

  it("parses and builds persistent project stage routes", () => {
    const route = parseRoute("/projects/project-1/workbench/documents");

    expect(route).toEqual({
      name: "project",
      projectId: "project-1",
      stage: "documents",
    });
    expect(routePath(route)).toBe("/projects/project-1/workbench/documents");
    expect(projectStagePath("project 1", "sources")).toBe(
      "/projects/project%201/workbench/sources",
    );
  });

  it("falls back to the overview stage when omitted", () => {
    expect(parseRoute("/projects/project-1/workbench")).toEqual({
      name: "project",
      projectId: "project-1",
      stage: "overview",
    });
  });

  it("keeps unknown routes explicit", () => {
    expect(parseRoute("/projects/project-1/workbench/release")).toEqual({
      name: "not-found",
      pathname: "/projects/project-1/workbench/release",
    });
  });
});
