import { requestJson } from "../../shared/api/client";
import type { ComparisonResult, ImpactAssessment } from "./types";

function comparisonPayload(baselineRunId: string, targetRunId: string): string {
  return JSON.stringify({
    baseline_run_id: baselineRunId,
    target_run_id: targetRunId,
  });
}

export function compareSnapshots(
  projectId: string,
  baselineRunId: string,
  targetRunId: string,
): Promise<ComparisonResult> {
  return requestJson<ComparisonResult>(`/projects/${projectId}/comparisons`, {
    method: "POST",
    body: comparisonPayload(baselineRunId, targetRunId),
  });
}

export function assessChangeImpact(
  projectId: string,
  baselineRunId: string,
  targetRunId: string,
): Promise<ImpactAssessment> {
  return requestJson<ImpactAssessment>(`/projects/${projectId}/comparisons/impact`, {
    method: "POST",
    body: comparisonPayload(baselineRunId, targetRunId),
  });
}
