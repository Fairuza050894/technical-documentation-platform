import { requestJson } from "../../shared/api/client";
import type {
  GeneratedDocumentCollection,
  GeneratedDocumentDetail,
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
): Promise<GeneratedDocumentDetail> {
  return requestJson<GeneratedDocumentDetail>(
    `/projects/${projectId}/documents/technical-source-overview`,
    {
      method: "POST",
      body: JSON.stringify({
        target_run_id: targetRunId,
        baseline_run_id: baselineRunId,
      }),
    },
  );
}

export function getGeneratedDocument(
  documentId: string,
): Promise<GeneratedDocumentDetail> {
  return requestJson<GeneratedDocumentDetail>(`/documents/${documentId}`);
}

export function getDocumentDownloadUrl(documentId: string): string {
  return `http://127.0.0.1:8000/api/documents/${encodeURIComponent(documentId)}/download`;
}
