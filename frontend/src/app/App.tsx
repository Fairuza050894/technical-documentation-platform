import { useCallback, useEffect, useState } from "react";

import type { OverviewNavigationTarget } from "../modules/overview/OperationalOverview";
import type { Project } from "../modules/projects/types";
import { listWorkspaces } from "../modules/workspaces/api";
import type { Workspace } from "../modules/workspaces/types";
import { AppShell } from "./components/AppShell";
import { RouteContent } from "./components/RouteContent";
import { useHealthStatus } from "./hooks/useHealthStatus";
import {
  buildNavigationGroups,
  resolveGlobalNavigation,
  resolvePageContext,
} from "./navigation";
import {
  type AppRoute,
  type ProjectStage,
  parseRoute,
  routePath,
  routeWorkspaceId,
} from "./router";
import type { Navigate, WorkspaceLoadState } from "./types";

const LAST_WORKSPACE_KEY = "tdp.last-workspace-id";

export function App() {
  const apiState = useHealthStatus();
  const [route, setRoute] = useState<AppRoute>(() =>
    parseRoute(globalThis.location.pathname),
  );
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string | null>(null);
  const [workspaceLoadState, setWorkspaceLoadState] =
    useState<WorkspaceLoadState>("loading");
  const [workspaceLoadError, setWorkspaceLoadError] = useState("");

  const navigate = useCallback<Navigate>((nextRoute, replace = false): void => {
    const path = routePath(nextRoute);
    if (replace) {
      globalThis.history.replaceState({}, "", path);
    } else {
      globalThis.history.pushState({}, "", path);
    }
    if (nextRoute.name !== "project") {
      setActiveProject(null);
    }
    const nextWorkspaceId = routeWorkspaceId(nextRoute);
    if (nextWorkspaceId !== null) {
      setActiveWorkspaceId(nextWorkspaceId);
      globalThis.localStorage.setItem(LAST_WORKSPACE_KEY, nextWorkspaceId);
    }
    setRoute(nextRoute);
  }, []);

  useEffect(() => {
    const handlePopState = (): void => {
      const nextRoute = parseRoute(globalThis.location.pathname);
      if (nextRoute.name !== "project") {
        setActiveProject(null);
      }
      const nextWorkspaceId = routeWorkspaceId(nextRoute);
      if (nextWorkspaceId !== null) {
        setActiveWorkspaceId(nextWorkspaceId);
        globalThis.localStorage.setItem(LAST_WORKSPACE_KEY, nextWorkspaceId);
      }
      setRoute(nextRoute);
    };

    globalThis.addEventListener("popstate", handlePopState);
    return () => globalThis.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
  }, [route]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadWorkspaceContext(): Promise<void> {
      setWorkspaceLoadState("loading");
      setWorkspaceLoadError("");
      try {
        const response = await listWorkspaces(controller.signal);
        const requestedId = routeWorkspaceId(
          parseRoute(globalThis.location.pathname),
        );
        const storedId = globalThis.localStorage.getItem(LAST_WORKSPACE_KEY);
        const requestedWorkspace =
          requestedId === null
            ? null
            : response.items.find(
                (workspace) => workspace.id === requestedId,
              ) ?? null;
        const selected =
          requestedId !== null
            ? requestedWorkspace
            : response.items.find(
                  (workspace) =>
                    workspace.id === storedId && workspace.status === "ACTIVE",
                ) ??
                response.items.find(
                  (workspace) => workspace.status === "ACTIVE",
                ) ??
                response.items[0] ??
                null;

        setWorkspaces(response.items);
        setActiveWorkspaceId(selected?.id ?? null);
        if (selected !== null) {
          globalThis.localStorage.setItem(LAST_WORKSPACE_KEY, selected.id);
        }
        setWorkspaceLoadState("ready");

        const currentRoute = parseRoute(globalThis.location.pathname);
        if (
          selected !== null &&
          currentRoute.name === "home" &&
          currentRoute.workspaceId === null
        ) {
          navigate({ name: "home", workspaceId: selected.id }, true);
        } else if (
          selected !== null &&
          currentRoute.name === "projects" &&
          currentRoute.workspaceId === null
        ) {
          navigate({ name: "projects", workspaceId: selected.id }, true);
        }
      } catch (error: unknown) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setWorkspaceLoadError(
          error instanceof Error
            ? error.message
            : "Workspace context could not be loaded.",
        );
        setWorkspaceLoadState("error");
      }
    }

    void loadWorkspaceContext();
    return () => controller.abort();
  }, [navigate]);

  const activeWorkspace =
    workspaces.find((workspace) => workspace.id === activeWorkspaceId) ?? null;

  const handleProjectResolved = useCallback(
    (project: Project | null): void => {
      setActiveProject(project);
      if (
        project !== null &&
        project.workspace_id !== undefined &&
        route.name === "project" &&
        route.workspaceId === null
      ) {
        setActiveWorkspaceId(project.workspace_id);
        globalThis.localStorage.setItem(
          LAST_WORKSPACE_KEY,
          project.workspace_id,
        );
        navigate(
          {
            name: "project",
            workspaceId: project.workspace_id,
            projectId: project.id,
            stage: route.stage,
          },
          true,
        );
      }
    },
    [navigate, route],
  );

  const selectWorkspace = useCallback(
    (workspace: Workspace): void => {
      setActiveWorkspaceId(workspace.id);
      setActiveProject(null);
      globalThis.localStorage.setItem(LAST_WORKSPACE_KEY, workspace.id);
      navigate({ name: "home", workspaceId: workspace.id });
    },
    [navigate],
  );

  const handleWorkspacesChanged = useCallback((items: Workspace[]): void => {
    setWorkspaces(items);
  }, []);

  function navigateFromOverview(
    target: OverviewNavigationTarget,
    projectId?: string,
  ): void {
    if (activeWorkspace === null) {
      navigate({ name: "workspaces" });
      return;
    }

    if (target === "Projects") {
      navigate(
        projectId
          ? {
              name: "project",
              workspaceId: activeWorkspace.id,
              projectId,
              stage: "overview",
            }
          : { name: "projects", workspaceId: activeWorkspace.id },
      );
      return;
    }

    if (!projectId) {
      navigate({ name: "projects", workspaceId: activeWorkspace.id });
      return;
    }

    const stageByTarget: Record<
      Exclude<OverviewNavigationTarget, "Projects">,
      ProjectStage
    > = {
      Sources: "sources",
      "API Catalog": "catalog",
      Changes: "changes",
      Documents: "documents",
    };
    navigate({
      name: "project",
      workspaceId: activeWorkspace.id,
      projectId,
      stage: stageByTarget[target],
    });
  }

  const navigationGroups = buildNavigationGroups(activeWorkspace?.id ?? null);
  const activeGlobalNavigation = resolveGlobalNavigation(route);
  const environment =
    apiState.status === "available" ? apiState.health.environment : "local";
  const serviceLabel =
    apiState.status === "loading"
      ? "Checking"
      : apiState.status === "available"
        ? "Connected"
        : "Offline";
  const pageContext = resolvePageContext(
    route,
    activeWorkspace,
    activeProject,
  );

  return (
    <AppShell
      workspaces={workspaces}
      activeWorkspaceId={activeWorkspaceId}
      activeWorkspace={activeWorkspace}
      activeProject={activeProject}
      workspaceLoadState={workspaceLoadState}
      workspaceLoadError={workspaceLoadError}
      navigationGroups={navigationGroups}
      activeGlobalNavigation={activeGlobalNavigation}
      pageContext={pageContext}
      route={route}
      apiState={apiState}
      serviceLabel={serviceLabel}
      environment={environment}
      onSelectWorkspace={selectWorkspace}
      onManageWorkspaces={() => navigate({ name: "workspaces" })}
      onNavigate={navigate}
    >
      <RouteContent
        route={route}
        apiState={apiState}
        workspaceLoadState={workspaceLoadState}
        workspaceLoadError={workspaceLoadError}
        activeWorkspace={activeWorkspace}
        activeWorkspaceId={activeWorkspaceId}
        onNavigate={navigate}
        onOverviewNavigate={navigateFromOverview}
        onSelectWorkspace={selectWorkspace}
        onWorkspacesChanged={handleWorkspacesChanged}
        onProjectResolved={handleProjectResolved}
      />
    </AppShell>
  );
}
