import { requestJson } from "../../shared/api/client";
import type {
  CreateRequirementInput,
  Requirement,
  RequirementCollection,
  TraceTargetType,
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

export function addRequirementTraceLink(
  workspaceId: string,
  projectId: string,
  requirementId: string,
  targetType: TraceTargetType,
  targetReference: string,
): Promise<Requirement> {
  const relationByTarget: Record<TraceTargetType, "IMPLEMENTED_BY" | "VERIFIED_BY" | "DOCUMENTED_BY"> = {
    FEATURE: "IMPLEMENTED_BY",
    EVIDENCE: "VERIFIED_BY",
    DOCUMENT: "DOCUMENTED_BY",
  };
  return requestJson<Requirement>(
    `${requirementBasePath(workspaceId, projectId)}/${encodeURIComponent(requirementId)}/trace-links`,
    {
      method: "POST",
      body: JSON.stringify({
        target_type: targetType,
        relation: relationByTarget[targetType],
        target_reference: targetReference.trim(),
      }),
    },
  );
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
