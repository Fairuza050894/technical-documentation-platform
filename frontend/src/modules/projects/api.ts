import { requestJson } from "../../shared/api/client";
import type { CreateProjectInput, Project, ProjectCollection } from "./types";

export function listProjects(signal?: AbortSignal): Promise<ProjectCollection> {
  return requestJson<ProjectCollection>("/projects", { signal });
}

export function createProject(input: CreateProjectInput): Promise<Project> {
  return requestJson<Project>("/projects", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function archiveProject(projectId: string): Promise<Project> {
  return requestJson<Project>(`/projects/${projectId}/archive`, { method: "POST" });
}
