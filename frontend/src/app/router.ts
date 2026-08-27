export const projectStages = [
  "overview",
  "features",
  "sources",
  "catalog",
  "changes",
  "documents",
  "evidence",
] as const;

export type ProjectStage = (typeof projectStages)[number];

export type AppRoute =
  | { name: "home"; workspaceId: string | null }
  | { name: "projects"; workspaceId: string | null }
  | { name: "workspaces" }
  | { name: "system" }
  | { name: "audit" }
  | { name: "login" }
  | {
      name: "project";
      workspaceId: string | null;
      projectId: string;
      stage: ProjectStage;
      featureId?: string | null;
    }
  | { name: "not-found"; pathname: string };

const workspaceHomePattern = /^\/workspaces\/([^/]+)\/?$/;
const workspaceProjectsPattern = /^\/workspaces\/([^/]+)\/projects\/?$/;
const workspaceProjectPattern =
  /^\/workspaces\/([^/]+)\/projects\/([^/]+)\/workbench(?:\/([^/]+))?(?:\/([^/]+))?\/?$/;
const legacyProjectPattern =
  /^\/projects\/([^/]+)\/workbench(?:\/([^/]+))?(?:\/([^/]+))?\/?$/;

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
  if (normalized === "/audit") {
    return { name: "audit" };
  }
  if (normalized === "/login") {
    return { name: "login" };
  }

  const workspaceProjectMatch = normalized.match(workspaceProjectPattern);
  if (workspaceProjectMatch) {
    const workspaceId = safeDecode(workspaceProjectMatch[1]);
    const projectId = safeDecode(workspaceProjectMatch[2]);
    const stage = workspaceProjectMatch[3] ?? "overview";
    const featureId = safeDecode(workspaceProjectMatch[4]);
    if (
      workspaceId !== null &&
      projectId !== null &&
      isProjectStage(stage) &&
      isValidFeatureContext(stage, featureId)
    ) {
      return featureId === null
        ? { name: "project", workspaceId, projectId, stage }
        : { name: "project", workspaceId, projectId, stage, featureId };
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
    const featureId = safeDecode(legacyProjectMatch[3]);
    if (
      projectId !== null &&
      isProjectStage(stage) &&
      isValidFeatureContext(stage, featureId)
    ) {
      return featureId === null
        ? { name: "project", workspaceId: null, projectId, stage }
        : { name: "project", workspaceId: null, projectId, stage, featureId };
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
    case "audit":
      return "/audit";
    case "login":
      return "/login";
    case "project":
      return route.workspaceId === null
        ? projectStagePath(route.projectId, route.stage, route.featureId)
        : workspaceProjectStagePath(
            route.workspaceId,
            route.projectId,
            route.stage,
            route.featureId,
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
  featureId?: string | null,
): string {
  const base = `${workspaceProjectsPath(workspaceId)}/${encodeURIComponent(projectId)}/workbench/${stage}`;
  return stage === "features" && featureId
    ? `${base}/${encodeURIComponent(featureId)}`
    : base;
}

export function projectStagePath(
  projectId: string,
  stage: ProjectStage,
  featureId?: string | null,
): string {
  const base = `/projects/${encodeURIComponent(projectId)}/workbench/${stage}`;
  return stage === "features" && featureId
    ? `${base}/${encodeURIComponent(featureId)}`
    : base;
}

export function routeWorkspaceId(route: AppRoute): string | null {
  switch (route.name) {
    case "home":
    case "projects":
    case "project":
      return route.workspaceId;
    case "workspaces":
    case "system":
    case "audit":
    case "login":
    case "not-found":
      return null;
  }
}

export function isProjectStage(value: string): value is ProjectStage {
  return projectStages.includes(value as ProjectStage);
}

function isValidFeatureContext(
  stage: ProjectStage,
  featureId: string | null,
): boolean {
  return featureId === null || stage === "features";
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