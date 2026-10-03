import { requestJson } from "../../shared/api/client";
import type {
  ProjectTraceability,
  Requirement,
  RequirementCollection,
  RequirementType,
  WorkflowCollection,
  WorkflowItem,
} from "./types";

export interface CreateRequirementInput {
  key: string;
  requirement_type: RequirementType;
  title: string;
  statement: string;
  acceptance_criteria: string[];
  rationale: string;
  feature_id: string | null;
}

function requirementBase(workspaceId: string, projectId: string): string {
  return `/workspaces/${encodeURIComponent(workspaceId)}/projects/${encodeURIComponent(projectId)}/requirements`;
}

function workflowBase(workspaceId: string, projectId: string): string {
  return `/workspaces/${encodeURIComponent(workspaceId)}/projects/${encodeURIComponent(projectId)}/workflow-items`;
}

export function listRequirements(
  workspaceId: string,
  projectId: string,
  signal?: AbortSignal,
): Promise<RequirementCollection> {
  return requestJson<RequirementCollection>(requirementBase(workspaceId, projectId), { signal });
}

export function createRequirement(
  workspaceId: string,
  projectId: string,
  input: CreateRequirementInput,
): Promise<Requirement> {
  return requestJson<Requirement>(requirementBase(workspaceId, projectId), {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function transitionRequirement(
  workspaceId: string,
  projectId: string,
  requirementId: string,
  action: "APPROVE" | "RETIRE",
): Promise<Requirement> {
  return requestJson<Requirement>(
    `${requirementBase(workspaceId, projectId)}/${encodeURIComponent(requirementId)}/transition`,
    {
      method: "POST",
      body: JSON.stringify({ action }),
    },
  );
}

export function getProjectTraceability(
  workspaceId: string,
  projectId: string,
  signal?: AbortSignal,
): Promise<ProjectTraceability> {
  return requestJson<ProjectTraceability>(`${requirementBase(workspaceId, projectId)}/traceability`, {
    signal,
  });
}

export function listWorkflowItems(
  workspaceId: string,
  projectId: string,
  signal?: AbortSignal,
): Promise<WorkflowCollection> {
  return requestJson<WorkflowCollection>(workflowBase(workspaceId, projectId), { signal });
}

export function createRequirementWorkflowItem(
  workspaceId: string,
  projectId: string,
  requirement: Requirement,
): Promise<WorkflowItem> {
  return requestJson<WorkflowItem>(workflowBase(workspaceId, projectId), {
    method: "POST",
    body: JSON.stringify({
      entity_type: "REQUIREMENT",
      entity_id: requirement.id,
      title: `Review ${requirement.key}: ${requirement.title}`,
      priority: requirement.requirement_type === "COMPLIANCE" ? "P1" : "P2",
      assignee: "",
    }),
  });
}
