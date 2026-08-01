import { useCallback, useEffect, useState } from "react";

import { OperationalOverview, type OverviewNavigationTarget } from "../modules/overview/OperationalOverview";
import { ProjectWorkspace } from "../modules/projects/ProjectWorkspace";
import type { Project } from "../modules/projects/types";
import { WorkspaceRegistry } from "../modules/workspaces/WorkspaceRegistry";
import { WorkspaceSwitcher } from "../modules/workspaces/WorkspaceSwitcher";
import { listWorkspaces } from "../modules/workspaces/api";
import type { Workspace } from "../modules/workspaces/types";
import { ProjectWorkbench } from "../modules/workbench/ProjectWorkbench";
import { Icon, type IconName } from "../shared/ui/Icon";
import {
  type AppRoute,
  type ProjectStage,
  parseRoute,
  routePath,
  routeWorkspaceId,
} from "./router";

interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
  environment: string;
}

type ApiState =
  | { status: "loading" }
  | { status: "available"; health: HealthResponse }
  | { status: "unavailable" };

type GlobalNavigation = "Home" | "Projects" | "System status";
type WorkspaceLoadState = "loading" | "ready" | "error";

const projectStageLabels: Record<ProjectStage, string> = {
  overview: "Overview",
  features: "Features",
  sources: "Sources",
  catalog: "API Catalog",
  changes: "Changes",
  documents: "Documents",
};

const projectStageIcons: Record<ProjectStage, IconName> = {
  overview: "overview",
  features: "projects",
  sources: "source",
  catalog: "catalog",
  changes: "changes",
  documents: "documents",
};

const LAST_WORKSPACE_KEY = "tdp.last-workspace-id";

export function App() {
  const [apiState, setApiState] = useState<ApiState>({ status: "loading" });
  const [route, setRoute] = useState<AppRoute>(() => parseRoute(globalThis.location.pathname));
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string | null>(null);
  const [workspaceLoadState, setWorkspaceLoadState] =
    useState<WorkspaceLoadState>("loading");
  const [workspaceLoadError, setWorkspaceLoadError] = useState("");

  const navigate = useCallback((nextRoute: AppRoute, replace = false): void => {
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

    async function loadHealth(): Promise<void> {
      try {
        const response = await fetch("http://127.0.0.1:8000/api/health", {
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error(`Health request failed with ${response.status}`);
        }
        const health = (await response.json()) as HealthResponse;
        setApiState({ status: "available", health });
      } catch (error: unknown) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setApiState({ status: "unavailable" });
      }
    }

    void loadHealth();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function loadWorkspaceContext(): Promise<void> {
      setWorkspaceLoadState("loading");
      setWorkspaceLoadError("");
      try {
        const response = await listWorkspaces(controller.signal);
        const requestedId = routeWorkspaceId(parseRoute(globalThis.location.pathname));
        const storedId = globalThis.localStorage.getItem(LAST_WORKSPACE_KEY);
        const requestedWorkspace =
          requestedId === null
            ? null
            : response.items.find((workspace) => workspace.id === requestedId) ?? null;
        const selected =
          requestedId !== null
            ? requestedWorkspace
            : response.items.find(
                  (workspace) => workspace.id === storedId && workspace.status === "ACTIVE",
                ) ??
                response.items.find((workspace) => workspace.status === "ACTIVE") ??
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
          error instanceof Error ? error.message : "Workspace context could not be loaded.",
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
        globalThis.localStorage.setItem(LAST_WORKSPACE_KEY, project.workspace_id);
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
      globalThis.localStorage.setItem(LAST_WORKSPACE_KEY, workspace.id);
      navigate({ name: "home", workspaceId: workspace.id });
    },
    [navigate],
  );

  const handleWorkspacesChanged = useCallback((items: Workspace[]): void => {
    setWorkspaces(items);
    setActiveWorkspaceId((current) =>
      current !== null && !items.some((item) => item.id === current) ? null : current,
    );
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

    const stageByTarget: Record<Exclude<OverviewNavigationTarget, "Projects">, ProjectStage> = {
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

  const navigationGroups: ReadonlyArray<{
    label: string;
    items: ReadonlyArray<{
      id: GlobalNavigation;
      label: string;
      icon: IconName;
      route: AppRoute;
    }>;
  }> = [
    {
      label: "Workspace",
      items: [
        {
          id: "Home",
          label: "Home",
          icon: "overview",
          route: { name: "home", workspaceId: activeWorkspace?.id ?? null },
        },
        {
          id: "Projects",
          label: "Projects",
          icon: "projects",
          route: { name: "projects", workspaceId: activeWorkspace?.id ?? null },
        },
      ],
    },
    {
      label: "Platform",
      items: [
        {
          id: "System status",
          label: "System status",
          icon: "server",
          route: { name: "system" },
        },
      ],
    },
  ];

  const activeGlobalNavigation = resolveGlobalNavigation(route);
  const environment = apiState.status === "available" ? apiState.health.environment : "local";
  const serviceLabel =
    apiState.status === "loading"
      ? "Checking"
      : apiState.status === "available"
        ? "Connected"
        : "Offline";
  const pageContext = resolvePageContext(route, activeWorkspace, activeProject);

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="product-mark" aria-label="Technical Documentation Platform">
          <span className="product-mark__symbol" aria-hidden="true">
            <Icon name="documents" size={17} />
          </span>
          <span className="product-mark__copy">
            <strong>Technical Docs</strong>
            <small>Documentation platform</small>
          </span>
        </div>

        <WorkspaceSwitcher
          workspaces={workspaces}
          activeWorkspaceId={activeWorkspaceId}
          status={workspaceLoadState}
          errorMessage={workspaceLoadError}
          onSelect={selectWorkspace}
          onManage={() => navigate({ name: "workspaces" })}
        />

        <nav className="primary-navigation">
          {navigationGroups.map((group) => (
            <section
              className="navigation-group"
              aria-labelledby={`nav-${group.label.replaceAll(" ", "-")}`}
              key={group.label}
            >
              <h2 id={`nav-${group.label.replaceAll(" ", "-")}`}>{group.label}</h2>
              <ul className="navigation-list">
                {group.items.map((item) => (
                  <li key={item.id}>
                    <button
                      type="button"
                      className={
                        item.id === activeGlobalNavigation
                          ? "navigation-item is-active"
                          : "navigation-item"
                      }
                      aria-current={item.id === activeGlobalNavigation ? "page" : undefined}
                      onClick={() => navigate(item.route)}
                    >
                      <span className="navigation-item__icon" aria-hidden="true">
                        <Icon name={item.icon} size={17} />
                      </span>
                      <span className="navigation-item__label">{item.label}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </nav>

        <div className="sidebar-service" aria-label={`Backend API ${serviceLabel}`}>
          <span className="sidebar-service__icon" aria-hidden="true">
            <Icon name="server" size={16} />
          </span>
          <span className="sidebar-service__copy">
            <strong>Backend API</strong>
            <small>
              {apiState.status === "loading" && "Checking service"}
              {apiState.status === "available" && `v${apiState.health.version}`}
              {apiState.status === "unavailable" && "Not connected"}
            </small>
          </span>
          <span
            className={
              apiState.status === "available"
                ? "service-dot service-dot--available"
                : "service-dot"
            }
            aria-hidden="true"
          />
        </div>
      </aside>

      <div className="application-frame">
        <header className="utility-bar">
          <div className="breadcrumb" aria-label="Breadcrumb">
            {pageContext.breadcrumb.map((item, index) => (
              <span className="breadcrumb__segment" key={`${item}-${index}`}>
                {index > 0 && <span aria-hidden="true">/</span>}
                {index === pageContext.breadcrumb.length - 1 ? (
                  <strong>
                    <Icon name={pageContext.icon} size={15} />
                    {item}
                  </strong>
                ) : (
                  <span>{item}</span>
                )}
              </span>
            ))}
          </div>

          <div className="utility-status" aria-label="Runtime context">
            <span className="utility-status__item">
              <span className="utility-status__label">Scope</span>
              <strong>
                {route.name === "project"
                  ? activeProject?.key ?? "Project"
                  : activeWorkspace?.key ?? "No workspace"}
              </strong>
            </span>
            <span className="utility-status__divider" aria-hidden="true" />
            <span className="utility-status__item">
              <span className="utility-status__label">Environment</span>
              <strong>{environment}</strong>
            </span>
            <span className="utility-status__divider" aria-hidden="true" />
            <span
              className={
                apiState.status === "available"
                  ? "runtime-state runtime-state--success"
                  : apiState.status === "unavailable"
                    ? "runtime-state runtime-state--danger"
                    : "runtime-state"
              }
            >
              <span className="runtime-state__dot" aria-hidden="true" />
              {serviceLabel}
            </span>
          </div>
        </header>

        <main className="main-content">
          <div className="workspace-canvas">
            {workspaceLoadState === "error" && route.name !== "system" && (
              <WorkspaceContextError
                message={workspaceLoadError}
                onManage={() => navigate({ name: "workspaces" })}
              />
            )}

            {workspaceLoadState === "loading" && route.name !== "system" && (
              <div className="project-workbench-state" role="status">
                <span className="loading-bar" aria-hidden="true" />
                Loading workspace context…
              </div>
            )}

            {workspaceLoadState === "ready" && route.name === "home" && (
              activeWorkspace === null ? (
                <WorkspaceContextError
                  message="Select an active workspace before opening Home."
                  onManage={() => navigate({ name: "workspaces" })}
                />
              ) : (
                <OperationalOverview
                  workspace={activeWorkspace}
                  serviceState={apiState.status}
                  serviceVersion={
                    apiState.status === "available" ? apiState.health.version : undefined
                  }
                  onNavigate={navigateFromOverview}
                />
              )
            )}

            {workspaceLoadState === "ready" && route.name === "projects" && (
              activeWorkspace === null ? (
                <WorkspaceContextError
                  message="Select an active workspace before opening Projects."
                  onManage={() => navigate({ name: "workspaces" })}
                />
              ) : (
                <ProjectWorkspace
                  workspace={activeWorkspace}
                  onOpenProject={(project) =>
                    navigate({
                      name: "project",
                      workspaceId: activeWorkspace.id,
                      projectId: project.id,
                      stage: "overview",
                    })
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
                  navigate({
                    name: "project",
                    workspaceId: route.workspaceId ?? activeWorkspace?.id ?? null,
                    projectId: route.projectId,
                    stage,
                  })
                }
                onNavigateFeature={(featureId) =>
                  navigate({
                    name: "project",
                    workspaceId: route.workspaceId ?? activeWorkspace?.id ?? null,
                    projectId: route.projectId,
                    stage: "features",
                    featureId,
                  })
                }
                onBackToProjects={() =>
                  navigate({
                    name: "projects",
                    workspaceId: route.workspaceId ?? activeWorkspace?.id ?? null,
                  })
                }
                onProjectResolved={handleProjectResolved}
              />
            )}

            {workspaceLoadState === "ready" && route.name === "workspaces" && (
              <WorkspaceRegistry
                activeWorkspaceId={activeWorkspaceId}
                onSelectWorkspace={selectWorkspace}
                onWorkspacesChanged={handleWorkspacesChanged}
              />
            )}

            {route.name === "system" && <SystemStatus apiState={apiState} />}

            {workspaceLoadState === "ready" && route.name === "not-found" && (
              <RouteNotFound
                pathname={route.pathname}
                onGoHome={() =>
                  navigate(
                    {
                      name: "home",
                      workspaceId: activeWorkspace?.id ?? null,
                    },
                    true,
                  )
                }
              />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

function resolveGlobalNavigation(route: AppRoute): GlobalNavigation | null {
  switch (route.name) {
    case "home":
      return "Home";
    case "projects":
    case "project":
      return "Projects";
    case "workspaces":
      return null;
    case "system":
      return "System status";
    case "not-found":
      return null;
  }
}

function resolvePageContext(
  route: AppRoute,
  workspace: Workspace | null,
  project: Project | null,
): { breadcrumb: string[]; icon: IconName } {
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

function WorkspaceContextError({
  message,
  onManage,
}: {
  message: string;
  onManage: () => void;
}) {
  return (
    <section
      className="content-section project-workbench-state"
      aria-labelledby="workspace-context-error-title"
    >
      <span className="project-workbench-state__icon" aria-hidden="true">
        <Icon name="alert" size={22} />
      </span>
      <h1 id="workspace-context-error-title">Workspace context unavailable</h1>
      <p>{message}</p>
      <button type="button" className="button button--primary" onClick={onManage}>
        Manage workspaces
      </button>
    </section>
  );
}

function RouteNotFound({ pathname, onGoHome }: { pathname: string; onGoHome: () => void }) {
  return (
    <section className="content-section project-workbench-state" aria-labelledby="route-not-found-title">
      <span className="project-workbench-state__icon" aria-hidden="true">
        <Icon name="alert" size={22} />
      </span>
      <h1 id="route-not-found-title">Page not found</h1>
      <p>
        No workspace route matches <code>{pathname}</code>.
      </p>
      <button type="button" className="button button--primary" onClick={onGoHome}>
        Return home
      </button>
    </section>
  );
}

function SystemStatus({ apiState }: { apiState: ApiState }) {
  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">Platform runtime</p>
          <h1>System status</h1>
          <p className="page-summary">
            Runtime metadata and deterministic documentation policies.
          </p>
        </div>
        <span
          className={
            apiState.status === "available"
              ? "environment-badge environment-badge--success"
              : "environment-badge environment-badge--warning"
          }
        >
          <span className="environment-badge__dot" aria-hidden="true" />
          {apiState.status === "available" ? "Operational" : "Service unavailable"}
        </span>
      </header>

      <section className="content-section" aria-labelledby="runtime-status-title">
        <div className="section-heading">
          <div>
            <h2 id="runtime-status-title">Runtime status</h2>
            <p>Live metadata from the local backend health endpoint.</p>
          </div>
        </div>

        <dl className="system-status-grid">
          <div>
            <dt>Service</dt>
            <dd>
              {apiState.status === "available"
                ? apiState.health.service
                : "Technical Documentation Platform"}
            </dd>
          </div>
          <div>
            <dt>Availability</dt>
            <dd>
              {apiState.status === "loading" && "Checking"}
              {apiState.status === "available" && "Available"}
              {apiState.status === "unavailable" && "Offline"}
            </dd>
          </div>
          <div>
            <dt>Version</dt>
            <dd>{apiState.status === "available" ? apiState.health.version : "Unavailable"}</dd>
          </div>
          <div>
            <dt>Environment</dt>
            <dd>{apiState.status === "available" ? apiState.health.environment : "Local"}</dd>
          </div>
        </dl>
      </section>

      <section className="content-section" aria-labelledby="product-policy-title">
        <div className="section-heading">
          <div>
            <h2 id="product-policy-title">Documentation policy</h2>
            <p>Non-negotiable constraints for every generated artifact.</p>
          </div>
        </div>

        <dl className="constraint-list constraint-list--compact">
          <div>
            <dt>Source-backed facts</dt>
            <dd>Every generated fact keeps a verifiable source reference.</dd>
          </div>
          <div>
            <dt>Deterministic pipeline</dt>
            <dd>Parsing, normalization, comparison, and rendering do not depend on AI.</dd>
          </div>
          <div>
            <dt>Explicit uncertainty</dt>
            <dd>Missing or conflicting information is surfaced instead of invented.</dd>
          </div>
        </dl>
      </section>
    </>
  );
}
