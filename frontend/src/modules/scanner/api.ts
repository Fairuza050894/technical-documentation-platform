import { requestJson } from "../../shared/api/client";
import type { ScanCollection, ScanResult } from "./types";

export function startScan(repositoryUrl: string, branch = "main"): Promise<ScanResult> {
  return requestJson<ScanResult>("/scanner/scan", {
    method: "POST",
    body: JSON.stringify({ repository_url: repositoryUrl, branch }),
  });
}

export function listScans(signal?: AbortSignal): Promise<ScanCollection> {
  return requestJson<ScanCollection>("/scanner/scans", { signal });
}

export function getScan(scanId: string): Promise<ScanResult> {
  return requestJson<ScanResult>(`/scanner/scans/${scanId}`);
}

export function deleteScan(scanId: string): Promise<void> {
  return requestJson<void>(`/scanner/scans/${scanId}`, { method: "DELETE" });
}

export interface GeneratedDocument {
  id: string;
  scan_id: string;
  template_key: string;
  name: string;
  content: string;
  created_at: string;
}

export function generateDocuments(scanId: string, templateKeys: string[]): Promise<GeneratedDocument[]> {
  return requestJson<GeneratedDocument[]>(`/scanner/scans/${scanId}/generate`, {
    method: "POST",
    body: JSON.stringify({ template_keys: templateKeys }),
  });
}

export function listGeneratedDocuments(scanId: string): Promise<GeneratedDocument[]> {
  return requestJson<GeneratedDocument[]>(`/scanner/scans/${scanId}/documents`);
}

export function getDocument(docId: string): Promise<GeneratedDocument> {
  return requestJson<GeneratedDocument>(`/scanner/documents/${docId}`);
}

import type { ScanComparison } from "./types";

export function rescanScan(scanId: string): Promise<ScanResult> {
  return requestJson<ScanResult>(`/scanner/scans/${scanId}/rescan`, {
    method: "POST",
  });
}

export function compareScans(scanId: string, otherId: string): Promise<ScanComparison> {
  return requestJson<ScanComparison>(`/scanner/scans/${scanId}/compare/${otherId}`);
}
