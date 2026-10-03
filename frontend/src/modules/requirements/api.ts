import { requestJson } from "../../shared/api/client";
import type {
  CreateRequirementInput,
  Requirement,
  RequirementCollection,
  TraceabilityCoverage,
} from "./types";

function requirementBasePath(workspaceId: string, projectId: string): string {
  return `/workspaces/${encodeURIComponent(workspaceId)}/projects/${encodeURIComponent(projectId)}/requirements`;
}

export function listRequirements(
  workspaceId: string,
  projectId: string,
  signal?: AbortSignal,
): Promise<RequirementCollection> {
  return requestJson<RequirementCollection>(requirementBasePath(workspaceId, projectId), {
    signal,
  });
}

export function createRequirement(
  workspaceId: string,
  projectId: string,
  input: CreateRequirementInput,
): Promise<Requirement> {
  return requestJson<Requirement>(requirementBasePath(workspaceId, projectId), {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function getTraceabilityCoverage(
  workspaceId: string,
  projectId: string,
  signal?: AbortSignal,
): Promise<TraceabilityCoverage> {
  return requestJson<TraceabilityCoverage>(
    `${requirementBasePath(workspaceId, projectId)}/traceability/coverage`,
    { signal },
  );
}
