import { requestJson } from "../../shared/api/client";
import type { CreateWorkspaceInput, Workspace, WorkspaceCollection } from "./types";

export function listWorkspaces(signal?: AbortSignal): Promise<WorkspaceCollection> {
  return requestJson<WorkspaceCollection>("/workspaces", { signal });
}

export function createWorkspace(input: CreateWorkspaceInput): Promise<Workspace> {
  return requestJson<Workspace>("/workspaces", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function archiveWorkspace(workspaceId: string): Promise<Workspace> {
  return requestJson<Workspace>(`/workspaces/${workspaceId}/archive`, {
    method: "POST",
  });
}
