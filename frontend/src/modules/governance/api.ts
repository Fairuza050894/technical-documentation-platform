import { requestJson } from "../../shared/api/client";
import type {
  ChangeSurface,
  GovernanceSummary,
  ImpactAssessment,
  RequirementRevision,
  RequirementType,
  TraceLink,
  TraceTargetType,
  WorkflowCase,
  WorkflowState,
} from "./types";

export function getGovernanceSummary(projectId: string, signal?: AbortSignal): Promise<GovernanceSummary> {
  return requestJson<GovernanceSummary>(`/projects/${projectId}/governance-summary`, { signal });
}

export function createRequirement(
  projectId: string,
  payload: {
    requirement_type: RequirementType;
    title: string;
    statement: string;
    rationale: string;
  },
): Promise<RequirementRevision> {
  return requestJson<RequirementRevision>(`/projects/${projectId}/requirements`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createTraceLink(
  projectId: string,
  payload: {
    requirement_id: string;
    target_type: TraceTargetType;
    target_id: string;
    relation: string;
  },
): Promise<TraceLink> {
  return requestJson<TraceLink>(`/projects/${projectId}/trace-links`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createImpactAssessment(
  projectId: string,
  payload: { change_reference: string; surface: ChangeSurface },
): Promise<ImpactAssessment> {
  return requestJson<ImpactAssessment>(`/projects/${projectId}/impact-assessments`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createWorkflowCase(
  projectId: string,
  payload: { impact_assessment_id: string; owner: string },
): Promise<WorkflowCase> {
  return requestJson<WorkflowCase>(`/projects/${projectId}/workflow-cases`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function transitionWorkflowCase(
  caseId: string,
  payload: { target_state: WorkflowState; comment?: string },
): Promise<WorkflowCase> {
  return requestJson<WorkflowCase>(`/workflow-cases/${caseId}/transitions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
