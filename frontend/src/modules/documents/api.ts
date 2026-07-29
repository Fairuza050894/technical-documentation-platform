import { requestJson } from "../../shared/api/client";
import type {
  DocumentVersionComparison,
  GeneratedDocumentCollection,
  GeneratedDocumentDetail,
  WorkflowEventCollection,
} from "./types";

export function listGeneratedDocuments(
  projectId: string,
): Promise<GeneratedDocumentCollection> {
  return requestJson<GeneratedDocumentCollection>(`/projects/${projectId}/documents`);
}

export function generateTechnicalSourceOverview(
  projectId: string,
  targetRunId: string,
  baselineRunId: string | null,
  revisionReason: string,
  actor: string,
): Promise<GeneratedDocumentDetail> {
  return requestJson<GeneratedDocumentDetail>(
    `/projects/${projectId}/documents/technical-source-overview`,
    {
      method: "POST",
      body: JSON.stringify({
        target_run_id: targetRunId,
        baseline_run_id: baselineRunId,
        revision_reason: revisionReason,
        actor,
      }),
    },
  );
}

export function getGeneratedDocument(
  versionId: string,
): Promise<GeneratedDocumentDetail> {
  return requestJson<GeneratedDocumentDetail>(`/document-versions/${versionId}`);
}

export function getDocumentDownloadUrl(versionId: string): string {
  return `http://127.0.0.1:8000/api/document-versions/${encodeURIComponent(versionId)}/download`;
}

export function submitDocumentForReview(
  versionId: string,
  actor: string,
  comment: string,
): Promise<GeneratedDocumentDetail> {
  return workflowRequest(versionId, "submit-review", actor, comment);
}

export function requestDocumentChanges(
  versionId: string,
  actor: string,
  comment: string,
): Promise<GeneratedDocumentDetail> {
  return workflowRequest(versionId, "request-changes", actor, comment);
}

export function approveDocumentVersion(
  versionId: string,
  actor: string,
  comment: string,
): Promise<GeneratedDocumentDetail> {
  return workflowRequest(versionId, "approve", actor, comment);
}

export function supersedeDocumentVersion(
  versionId: string,
  actor: string,
  comment: string,
): Promise<GeneratedDocumentDetail> {
  return workflowRequest(versionId, "supersede", actor, comment);
}

export function listWorkflowEvents(versionId: string): Promise<WorkflowEventCollection> {
  return requestJson<WorkflowEventCollection>(
    `/document-versions/${versionId}/workflow-events`,
  );
}

export function compareDocumentVersions(
  baselineVersionId: string,
  targetVersionId: string,
): Promise<DocumentVersionComparison> {
  return requestJson<DocumentVersionComparison>("/document-version-comparisons", {
    method: "POST",
    body: JSON.stringify({
      baseline_version_id: baselineVersionId,
      target_version_id: targetVersionId,
    }),
  });
}

function workflowRequest(
  versionId: string,
  action: string,
  actor: string,
  comment: string,
): Promise<GeneratedDocumentDetail> {
  return requestJson<GeneratedDocumentDetail>(
    `/document-versions/${versionId}/${action}`,
    {
      method: "POST",
      body: JSON.stringify({ actor, comment }),
    },
  );
}
