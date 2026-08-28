import { AuditTrailViewer } from "../../modules/audit/AuditTrailViewer";
import { TemplateWorkspace } from "../../modules/templates/TemplateWorkspace";
import {
  OperationalOverview,
  type OverviewNavigationTarget,
} from "../../modules/overview/OperationalOverview";
import { ProjectWorkspace } from "../../modules/projects/ProjectWorkspace";
import type { Project } from "../../modules/projects/types";
import { WorkspaceRegistry } from "../../modules/workspaces/WorkspaceRegistry";
import type { Workspace } from "../../modules/workspaces/types";
import { ProjectWorkbench } from "../../modules/workbench/ProjectWorkbench";
import type { AppRoute, ProjectStage } from "../router";
import type { ApiState, Navigate, WorkspaceLoadState } from "../types";
import { RouteNotFound, WorkspaceContextError } from "./RouteStates";
import { SystemStatus } from "./SystemStatus";

interface RouteContentProps {
  route: AppRoute;
  apiState: ApiState;
  workspaceLoadState: WorkspaceLoadState;
  workspaceLoadError: string;
  activeWorkspace: Workspace | null;
  activeWorkspaceId: string | null;
  onNavigate: Navigate;
  onOverviewNavigate: (
    target: OverviewNavigationTarget,
    projectId?: string,
  ) => void;
  onSelectWorkspace: (workspace: Workspace) => void;
  onWorkspacesChanged: (workspaces: Workspace[]) => void;
  onProjectResolved: (project: Project | null) => void;
}

export function RouteContent({
  route,
  apiState,
  workspaceLoadState,
  workspaceLoadError,
  activeWorkspace,
  activeWorkspaceId,
  onNavigate,
  onOverviewNavigate,
  onSelectWorkspace,
  onWorkspacesChanged,
  onProjectResolved,
}: RouteContentProps) {
  const manageWorkspaces = (): void => onNavigate({ name: "workspaces" });
  const workspaceId =
    route.name === "project"
      ? route.workspaceId ?? activeWorkspace?.id ?? null
      : activeWorkspace?.id ?? null;

  const navigateProjectStage = (
    projectId: string,
    stage: ProjectStage,
  ): void => {
    onNavigate({
      name: "project",
      workspaceId,
      projectId,
      stage,
    });
  };

  return (
    <>
      {workspaceLoadState === "error" && route.name !== "system" && route.name !== "templates" && route.name !== "audit" && route.name !== "login" && (
        <WorkspaceContextError
          message={workspaceLoadError}
          onManage={manageWorkspaces}
        />
      )}

      {workspaceLoadState === "loading" && route.name !== "system" && route.name !== "templates" && route.name !== "audit" && route.name !== "login" && (
        <div className="project-workbench-state" role="status">
          <span className="loading-bar" aria-hidden="true" />
          Loading workspace context…
        </div>
      )}

      {workspaceLoadState === "ready" && route.name === "home" && (
        activeWorkspace === null ? (
          <WorkspaceContextError
            message="Select an active workspace before opening Home."
            onManage={manageWorkspaces}
          />
        ) : (
          <OperationalOverview
            workspace={activeWorkspace}
            serviceState={apiState.status}
            serviceVersion={
              apiState.status === "available" ? apiState.health.version : undefined
            }
            onNavigate={onOverviewNavigate}
          />
        )
      )}

      {workspaceLoadState === "ready" && route.name === "projects" && (
        activeWorkspace === null ? (
          <WorkspaceContextError
            message="Select an active workspace before opening Projects."
            onManage={manageWorkspaces}
          />
        ) : (
          <ProjectWorkspace
            workspace={activeWorkspace}
            onOpenProject={(project) =>
              navigateProjectStage(project.id, "overview")
            }
          />
        )
      )}

      {workspaceLoadState === "ready" && route.name === "project" && (
        <ProjectWorkbench
          workspaceId={route.workspaceId}
          projectId={route.projectId}
          stage={route.stage}
          featureId={route.featureId ?? null}
          onNavigateStage={(stage) =>
            navigateProjectStage(route.projectId, stage)
          }
          onNavigateFeature={(featureId) =>
            onNavigate({
              name: "project",
              workspaceId,
              projectId: route.projectId,
              stage: "features",
              featureId,
            })
          }
          onBackToProjects={() =>
            onNavigate({
              name: "projects",
              workspaceId,
            })
          }
          onProjectResolved={onProjectResolved}
        />
      )}

      {workspaceLoadState === "ready" && route.name === "workspaces" && (
        <WorkspaceRegistry
          activeWorkspaceId={activeWorkspaceId}
          onSelectWorkspace={onSelectWorkspace}
          onWorkspacesChanged={onWorkspacesChanged}
        />
      )}

      {route.name === "system" && <SystemStatus apiState={apiState} />}

      {route.name === "audit" && <AuditTrailViewer />}

      {route.name === "templates" && <TemplateWorkspace />}

      {workspaceLoadState === "ready" && route.name === "not-found" && (
        <RouteNotFound
          pathname={route.pathname}
          onGoHome={() =>
            onNavigate(
              {
                name: "home",
                workspaceId: activeWorkspace?.id ?? null,
              },
              true,
            )
          }
        />
      )}
    </>
  );
}