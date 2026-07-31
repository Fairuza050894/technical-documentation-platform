export const projectStages = [
  "overview",
  "sources",
  "catalog",
  "changes",
  "documents",
] as const;

export type ProjectStage = (typeof projectStages)[number];

export type AppRoute =
  | { name: "home"; workspaceId: string | null }
  | { name: "projects"; workspaceId: string | null }
  | { name: "workspaces" }
  | { name: "system" }
  | {
      name: "project";
      workspaceId: string | null;
      projectId: string;
      stage: ProjectStage;
    }
  | { name: "not-found"; pathname: string };

const workspaceHomePattern = /^\/workspaces\/([^/]+)\/?$/;
const workspaceProjectsPattern = /^\/workspaces\/([^/]+)\/projects\/?$/;
const workspaceProjectPattern =
  /^\/workspaces\/([^/]+)\/projects\/([^/]+)\/workbench(?:\/([^/]+))?\/?$/;
const legacyProjectPattern = /^\/projects\/([^/]+)\/workbench(?:\/([^/]+))?\/?$/;

export function parseRoute(pathname: string): AppRoute {
  const normalized = normalizePath(pathname);

  if (normalized === "/" || normalized === "/home") {
    return { name: "home", workspaceId: null };
  }
  if (normalized === "/projects") {
    return { name: "projects", workspaceId: null };
  }
  if (normalized === "/workspaces") {
    return { name: "workspaces" };
  }
  if (normalized === "/system") {
    return { name: "system" };
  }

  const workspaceProjectMatch = normalized.match(workspaceProjectPattern);
  if (workspaceProjectMatch) {
    const workspaceId = safeDecode(workspaceProjectMatch[1]);
    const projectId = safeDecode(workspaceProjectMatch[2]);
    const stage = workspaceProjectMatch[3] ?? "overview";
    if (
      workspaceId !== null &&
      projectId !== null &&
      isProjectStage(stage)
    ) {
      return { name: "project", workspaceId, projectId, stage };
    }
  }

  const workspaceProjectsMatch = normalized.match(workspaceProjectsPattern);
  if (workspaceProjectsMatch) {
    const workspaceId = safeDecode(workspaceProjectsMatch[1]);
    if (workspaceId !== null) {
      return { name: "projects", workspaceId };
    }
  }

  const workspaceHomeMatch = normalized.match(workspaceHomePattern);
  if (workspaceHomeMatch) {
    const workspaceId = safeDecode(workspaceHomeMatch[1]);
    if (workspaceId !== null) {
      return { name: "home", workspaceId };
    }
  }

  const legacyProjectMatch = normalized.match(legacyProjectPattern);
  if (legacyProjectMatch) {
    const projectId = safeDecode(legacyProjectMatch[1]);
    const stage = legacyProjectMatch[2] ?? "overview";
    if (projectId !== null && isProjectStage(stage)) {
      return { name: "project", workspaceId: null, projectId, stage };
    }
  }

  return { name: "not-found", pathname: normalized };
}

export function routePath(route: AppRoute): string {
  switch (route.name) {
    case "home":
      return route.workspaceId === null
        ? "/"
        : workspaceHomePath(route.workspaceId);
    case "projects":
      return route.workspaceId === null
        ? "/projects"
        : workspaceProjectsPath(route.workspaceId);
    case "workspaces":
      return "/workspaces";
    case "system":
      return "/system";
    case "project":
      return route.workspaceId === null
        ? `/projects/${encodeURIComponent(route.projectId)}/workbench/${route.stage}`
        : workspaceProjectStagePath(
            route.workspaceId,
            route.projectId,
            route.stage,
          );
    case "not-found":
      return route.pathname;
  }
}

export function workspaceHomePath(workspaceId: string): string {
  return `/workspaces/${encodeURIComponent(workspaceId)}`;
}

export function workspaceProjectsPath(workspaceId: string): string {
  return `${workspaceHomePath(workspaceId)}/projects`;
}

export function workspaceProjectStagePath(
  workspaceId: string,
  projectId: string,
  stage: ProjectStage,
): string {
  return `${workspaceProjectsPath(workspaceId)}/${encodeURIComponent(projectId)}/workbench/${stage}`;
}

export function projectStagePath(projectId: string, stage: ProjectStage): string {
  return `/projects/${encodeURIComponent(projectId)}/workbench/${stage}`;
}

export function routeWorkspaceId(route: AppRoute): string | null {
  switch (route.name) {
    case "home":
    case "projects":
    case "project":
      return route.workspaceId;
    case "workspaces":
    case "system":
    case "not-found":
      return null;
  }
}

export function isProjectStage(value: string): value is ProjectStage {
  return projectStages.includes(value as ProjectStage);
}

function safeDecode(value: string | undefined): string | null {
  if (value === undefined) {
    return null;
  }
  try {
    return decodeURIComponent(value);
  } catch {
    return null;
  }
}

function normalizePath(pathname: string): string {
  if (!pathname || pathname === "/") {
    return "/";
  }
  const withLeadingSlash = pathname.startsWith("/") ? pathname : `/${pathname}`;
  return withLeadingSlash.length > 1
    ? withLeadingSlash.replace(/\/+$/, "")
    : withLeadingSlash;
}
