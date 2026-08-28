import type { Project } from "../modules/projects/types";
import type { Workspace } from "../modules/workspaces/types";
import type { IconName } from "../shared/ui/Icon";
import type { AppRoute, ProjectStage } from "./router";

export type GlobalNavigation = "Home" | "Projects" | "Templates" | "System status" | "Audit trail";

export interface NavigationItem {
  id: GlobalNavigation;
  label: string;
  icon: IconName;
  route: AppRoute;
  adminOnly?: boolean;
}

export interface NavigationGroup {
  label: string;
  items: readonly NavigationItem[];
}

export interface PageContext {
  breadcrumb: string[];
  icon: IconName;
}

const projectStageLabels: Record<ProjectStage, string> = {
  overview: "Overview",
  features: "Features",
  sources: "Sources",
  catalog: "API Catalog",
  changes: "Changes",
  documents: "Documents",
  evidence: "Evidence",
};

const projectStageIcons: Record<ProjectStage, IconName> = {
  overview: "overview",
  features: "projects",
  sources: "source",
  catalog: "catalog",
  changes: "changes",
  documents: "documents",
  evidence: "documents",
};

export function buildNavigationGroups(activeWorkspaceId: string | null): readonly NavigationGroup[] {
  return [
    {
      label: "Workspace",
      items: [
        {
          id: "Home",
          label: "Home",
          icon: "overview",
          route: { name: "home", workspaceId: activeWorkspaceId },
        },
        {
          id: "Projects",
          label: "Projects",
          icon: "projects",
          route: { name: "projects", workspaceId: activeWorkspaceId },
        },
      ],
    },
    {
      label: "Platform",
      items: [
        {
          id: "Templates",
          label: "Templates",
          icon: "documents",
          route: { name: "templates" },
        },
        {
          id: "System status",
          label: "System status",
          icon: "server",
          route: { name: "system" },
        },
        {
          id: "Audit trail",
          label: "Audit trail",
          icon: "documents",
          route: { name: "audit" },
          adminOnly: true,
        },
      ],
    },
  ];
}

export function resolveGlobalNavigation(route: AppRoute): GlobalNavigation | null {
  switch (route.name) {
    case "home":
      return "Home";
    case "projects":
    case "project":
      return "Projects";
    case "workspaces":
      return null;
    case "templates":
      return "Templates";
    case "system":
      return "System status";
    case "audit":
      return "Audit trail";
    case "login":
      return null;
    case "not-found":
      return null;
  }
}

export function resolvePageContext(
  route: AppRoute,
  workspace: Workspace | null,
  project: Project | null,
): PageContext {
  const workspaceLabel = workspace?.key ?? "Workspace";
  switch (route.name) {
    case "home":
      return { breadcrumb: [workspaceLabel, "Home"], icon: "overview" };
    case "projects":
      return { breadcrumb: [workspaceLabel, "Projects"], icon: "projects" };
    case "workspaces":
      return { breadcrumb: ["Platform", "Workspaces"], icon: "folder" };
    case "system":
      return { breadcrumb: ["Platform", "System status"], icon: "server" };
    case "templates":
      return { breadcrumb: ["Platform", "Templates"], icon: "documents" };
    case "audit":
      return { breadcrumb: ["Platform", "Audit trail"], icon: "documents" };
    case "login":
      return { breadcrumb: ["Sign in"], icon: "documents" };
    case "project":
      return {
        breadcrumb: [
          workspaceLabel,
          "Projects",
          project?.key ?? "Project",
          projectStageLabels[route.stage],
        ],
        icon: projectStageIcons[route.stage],
      };
    case "not-found":
      return { breadcrumb: [workspaceLabel, "Not found"], icon: "alert" };
  }
}