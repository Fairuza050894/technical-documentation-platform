import { requestJson } from "../../shared/api/client";
import { apiUrl } from "../../shared/api/config";
import type {
  DocumentTypeRegistry,
  ProjectDocumentationChecklist,
} from "./types";

import type {
  DocumentVersionComparison,
  GeneratedDocumentCollection,
  GeneratedDocumentDetail,
  WorkflowEventCollection,
} from "./types";

export function listGeneratedDocuments(
  projectId: string,
  signal?: AbortSignal,
): Promise<GeneratedDocumentCollection> {
  return requestJson<GeneratedDocumentCollection>(`/projects/${projectId}/documents`, { signal });
}

export function generateTechnicalSourceOverview(
  projectId: string,
  targetRunId: string,
  baselineRunId: string | null,
  revisionReason: string,
): Promise<GeneratedDocumentDetail> {
  return requestJson<GeneratedDocumentDetail>(
    `/projects/${projectId}/documents/technical-source-overview`,
    {
      method: "POST",
      body: JSON.stringify({
        target_run_id: targetRunId,
        baseline_run_id: baselineRunId,
        revision_reason: revisionReason,
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
  return apiUrl(`/document-versions/${encodeURIComponent(versionId)}/download`);
}

export function submitDocumentForReview(
  versionId: string,
  comment: string,
): Promise<GeneratedDocumentDetail> {
  return workflowRequest(versionId, "submit-review", comment);
}

export function requestDocumentChanges(
  versionId: string,
  comment: string,
): Promise<GeneratedDocumentDetail> {
  return workflowRequest(versionId, "request-changes", comment);
}

export function approveDocumentVersion(
  versionId: string,
  comment: string,
): Promise<GeneratedDocumentDetail> {
  return workflowRequest(versionId, "approve", comment);
}

export function supersedeDocumentVersion(
  versionId: string,
  comment: string,
): Promise<GeneratedDocumentDetail> {
  return workflowRequest(versionId, "supersede", comment);
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
  comment: string,
): Promise<GeneratedDocumentDetail> {
  return requestJson<GeneratedDocumentDetail>(
    `/document-versions/${versionId}/${action}`,
    {
      method: "POST",
      body: JSON.stringify({ comment }),
    },
  );
}

export function listDocumentTypes(): Promise<DocumentTypeRegistry> {
  return requestJson<DocumentTypeRegistry>("/document-types");
}

export function getDocumentationChecklist(
  projectId: string,
): Promise<ProjectDocumentationChecklist> {
  return requestJson<ProjectDocumentationChecklist>(
    `/projects/${projectId}/documentation-checklist`,
  );
}

export function generateEnterpriseDocument(
  projectId: string,
  documentType: string,
  revisionReason: string,
): Promise<GeneratedDocumentDetail> {
  return requestJson<GeneratedDocumentDetail>(
    `/projects/${projectId}/documents/${documentType}/generate`,
    {
      method: "POST",
      body: JSON.stringify({ revision_reason: revisionReason }),
    },
  );
}
