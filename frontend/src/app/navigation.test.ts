import { describe, expect, it } from "vitest";

import {
  buildNavigationGroups,
  resolveGlobalNavigation,
  resolvePageContext,
} from "./navigation";
import type { AppRoute } from "./router";

describe("application navigation composition", () => {
  it("builds workspace-scoped global navigation", () => {
    const groups = buildNavigationGroups("workspace-1");

    expect(groups).toHaveLength(2);
    expect(groups[0]?.items[0]?.route).toEqual({
      name: "home",
      workspaceId: "workspace-1",
    });
    expect(groups[0]?.items[1]?.route).toEqual({
      name: "projects",
      workspaceId: "workspace-1",
    });
  });

  it("maps project routes to the Projects navigation item", () => {
    const route: AppRoute = {
      name: "project",
      workspaceId: "workspace-1",
      projectId: "project-1",
      stage: "documents",
    };

    expect(resolveGlobalNavigation(route)).toBe("Projects");
  });

  it("builds project breadcrumbs from stable route context", () => {
    const route: AppRoute = {
      name: "project",
      workspaceId: "workspace-1",
      projectId: "project-1",
      stage: "features",
    };

    expect(
      resolvePageContext(
        route,
        {
          id: "workspace-1",
          key: "ERP",
          name: "ERP",
          description: "",
          status: "ACTIVE",
          created_at: "2026-08-04T00:00:00Z",
          updated_at: "2026-08-04T00:00:00Z",
        },
        {
          id: "project-1",
          workspace_id: "workspace-1",
          key: "CORE",
          name: "ERP Core",
          description: "",
          ownership_type: "TEAM",
          status: "ACTIVE",
          created_at: "2026-08-04T00:00:00Z",
          updated_at: "2026-08-04T00:00:00Z",
        },
      ),
    ).toEqual({
      breadcrumb: ["ERP", "Projects", "CORE", "Features"],
      icon: "projects",
    });
  });
});
