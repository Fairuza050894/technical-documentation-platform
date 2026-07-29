export type WorkspaceType = "DEMO" | "PERSONAL" | "ENTERPRISE";
export type ProjectStatus = "ACTIVE" | "ARCHIVED";

export interface Project {
  id: string;
  key: string;
  name: string;
  description: string;
  workspace_type: WorkspaceType;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

export interface ProjectCollection {
  items: Project[];
  total: number;
}

export interface CreateProjectInput {
  key: string;
  name: string;
  description: string;
  workspace_type: WorkspaceType;
}
