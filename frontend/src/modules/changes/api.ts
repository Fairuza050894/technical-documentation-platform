import { requestJson } from "../../shared/api/client";
import type { ComparisonResult, ImpactAssessment } from "./types";

const payload = (baselineRunId: string, targetRunId: string) => ({
  baseline_run_id: baselineRunId,
  target_run_id: targetRunId,
});

export function compareSnapshots(
  projectId: string,
  baselineRunId: string,
  targetRunId: string,
): Promise<ComparisonResult> {
  return requestJson<ComparisonResult>(`/projects/${projectId}/comparisons`, {
    method: "POST",
    body: JSON.stringify(payload(baselineRunId, targetRunId)),
  });
}

export function assessImpact(
  projectId: string,
  baselineRunId: string,
  targetRunId: string,
): Promise<ImpactAssessment> {
  return requestJson<ImpactAssessment>(`/projects/${projectId}/impact-assessments`, {
    method: "POST",
    body: JSON.stringify(payload(baselineRunId, targetRunId)),
  });
}
