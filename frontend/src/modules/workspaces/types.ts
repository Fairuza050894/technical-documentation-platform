export type WorkspaceStatus = "ACTIVE" | "ARCHIVED";

export interface Workspace {
  id: string;
  key: string;
  name: string;
  description: string;
  status: WorkspaceStatus;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceCollection {
  items: Workspace[];
  total: number;
}

export interface CreateWorkspaceInput {
  key: string;
  name: string;
  description: string;
}
