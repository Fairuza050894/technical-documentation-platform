import type { ReactNode } from "react";

import type { Project } from "../../modules/projects/types";
import type { Workspace } from "../../modules/workspaces/types";
import type {
  GlobalNavigation,
  NavigationGroup,
  PageContext,
} from "../navigation";
import type { AppRoute } from "../router";
import type { ApiState, Navigate, WorkspaceLoadState } from "../types";
import { AppSidebar } from "./AppSidebar";
import { AppUtilityBar } from "./AppUtilityBar";

interface AppShellProps {
  children: ReactNode;
  workspaces: Workspace[];
  activeWorkspaceId: string | null;
  activeWorkspace: Workspace | null;
  activeProject: Project | null;
  workspaceLoadState: WorkspaceLoadState;
  workspaceLoadError: string;
  navigationGroups: readonly NavigationGroup[];
  activeGlobalNavigation: GlobalNavigation | null;
  pageContext: PageContext;
  route: AppRoute;
  apiState: ApiState;
  serviceLabel: string;
  environment: string;
  onSelectWorkspace: (workspace: Workspace) => void;
  onManageWorkspaces: () => void;
  onNavigate: Navigate;
}

export function AppShell({
  children,
  workspaces,
  activeWorkspaceId,
  activeWorkspace,
  activeProject,
  workspaceLoadState,
  workspaceLoadError,
  navigationGroups,
  activeGlobalNavigation,
  pageContext,
  route,
  apiState,
  serviceLabel,
  environment,
  onSelectWorkspace,
  onManageWorkspaces,
  onNavigate,
}: AppShellProps) {
  return (
    <>
    <a className="skip-to-content" href="#main-content">
      Skip to content
    </a>
    <div className="app-shell">
      <AppSidebar
        workspaces={workspaces}
        activeWorkspaceId={activeWorkspaceId}
        workspaceLoadState={workspaceLoadState}
        workspaceLoadError={workspaceLoadError}
        navigationGroups={navigationGroups}
        activeGlobalNavigation={activeGlobalNavigation}
        apiState={apiState}
        serviceLabel={serviceLabel}
        onSelectWorkspace={onSelectWorkspace}
        onManageWorkspaces={onManageWorkspaces}
        onNavigate={onNavigate}
      />

      <div className="application-frame">
        <AppUtilityBar
          pageContext={pageContext}
          route={route}
          activeWorkspace={activeWorkspace}
          activeProject={activeProject}
          environment={environment}
          apiState={apiState}
          serviceLabel={serviceLabel}
          onNavigate={onNavigate}
        />

        <main className="main-content" id="main-content" aria-label="Main content">
          <div className="workspace-canvas">{children}</div>
        </main>
      </div>
    </div>
    </>
  );
}
