import { requestJson } from "../../shared/api/client";
import type { CreateProjectInput, Project, ProjectCollection } from "./types";

export function listProjects(signal?: AbortSignal): Promise<ProjectCollection>;
export function listProjects(
  workspaceId: string,
  signal?: AbortSignal,
): Promise<ProjectCollection>;
export function listProjects(
  workspaceOrSignal?: string | AbortSignal,
  signal?: AbortSignal,
): Promise<ProjectCollection> {
  const workspaceId =
    typeof workspaceOrSignal === "string" ? workspaceOrSignal : undefined;
  const requestSignal =
    typeof workspaceOrSignal === "string" ? signal : workspaceOrSignal;
  const path =
    workspaceId === undefined
      ? "/projects"
      : `/workspaces/${encodeURIComponent(workspaceId)}/projects`;
  return requestJson<ProjectCollection>(path, { signal: requestSignal });
}

export function createProject(
  workspaceId: string,
  input: CreateProjectInput,
): Promise<Project> {
  return requestJson<Project>(
    `/workspaces/${encodeURIComponent(workspaceId)}/projects`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
}

export function getProject(projectId: string, signal?: AbortSignal): Promise<Project> {
  return requestJson<Project>(`/projects/${encodeURIComponent(projectId)}`, { signal });
}

export function archiveProject(projectId: string): Promise<Project> {
  return requestJson<Project>(`/projects/${encodeURIComponent(projectId)}/archive`, {
    method: "POST",
  });
}
