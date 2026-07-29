import { requestJson } from "../../shared/api/client";
import type { ApiCatalog, SynchronizationRun } from "./types";

interface SynchronizationCollection {
  items: SynchronizationRun[];
  total: number;
}

export function getApiCatalog(
  projectId: string,
  sourceId?: string,
  signal?: AbortSignal,
): Promise<ApiCatalog> {
  const search = sourceId ? `?source_id=${encodeURIComponent(sourceId)}` : "";
  return requestJson<ApiCatalog>(`/projects/${projectId}/api-catalog${search}`, { signal });
}

export function synchronizeSource(sourceId: string): Promise<SynchronizationRun> {
  return requestJson<SynchronizationRun>(`/sources/${sourceId}/synchronizations`, {
    method: "POST",
  });
}

export function listSynchronizations(sourceId: string): Promise<SynchronizationCollection> {
  return requestJson<SynchronizationCollection>(`/sources/${sourceId}/synchronizations`);
}
