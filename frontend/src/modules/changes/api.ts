import { requestJson } from "../../shared/api/client";
import type { ComparisonResult } from "./types";

export function compareSnapshots(
  projectId: string,
  baselineRunId: string,
  targetRunId: string,
): Promise<ComparisonResult> {
  return requestJson<ComparisonResult>(`/projects/${projectId}/comparisons`, {
    method: "POST",
    body: JSON.stringify({
      baseline_run_id: baselineRunId,
      target_run_id: targetRunId,
    }),
  });
}
