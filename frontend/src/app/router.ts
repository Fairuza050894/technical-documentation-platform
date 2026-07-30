export const projectStages = [
  "overview",
  "sources",
  "catalog",
  "changes",
  "documents",
] as const;

export type ProjectStage = (typeof projectStages)[number];

export type AppRoute =
  | { name: "home" }
  | { name: "projects" }
  | { name: "system" }
  | { name: "project"; projectId: string; stage: ProjectStage }
  | { name: "not-found"; pathname: string };

const projectRoutePattern = /^\/projects\/([^/]+)\/workbench(?:\/([^/]+))?\/?$/;

export function parseRoute(pathname: string): AppRoute {
  const normalized = normalizePath(pathname);

  if (normalized === "/" || normalized === "/home") {
    return { name: "home" };
  }
  if (normalized === "/projects") {
    return { name: "projects" };
  }
  if (normalized === "/system") {
    return { name: "system" };
  }

  const match = normalized.match(projectRoutePattern);
  if (match) {
    const encodedProjectId = match[1];
    const stage = match[2] ?? "overview";

    if (encodedProjectId !== undefined) {
      const projectId = safeDecode(encodedProjectId);
      if (projectId !== null && isProjectStage(stage)) {
        return { name: "project", projectId, stage };
      }
    }
  }

  return { name: "not-found", pathname: normalized };
}

export function routePath(route: AppRoute): string {
  switch (route.name) {
    case "home":
      return "/";
    case "projects":
      return "/projects";
    case "system":
      return "/system";
    case "project":
      return projectStagePath(route.projectId, route.stage);
    case "not-found":
      return route.pathname;
  }
}

export function projectStagePath(projectId: string, stage: ProjectStage): string {
  return `/projects/${encodeURIComponent(projectId)}/workbench/${stage}`;
}

export function isProjectStage(value: string): value is ProjectStage {
  return projectStages.includes(value as ProjectStage);
}

function safeDecode(value: string): string | null {
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
