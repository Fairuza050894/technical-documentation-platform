import { requestJson } from "../../shared/api/client";
import type { SourceCollection, TechnicalSource } from "./types";

export function listSources(projectId: string, signal?: AbortSignal): Promise<SourceCollection> {
  return requestJson<SourceCollection>(`/projects/${projectId}/sources`, { signal });
}

export function importOpenApiSource(
  projectId: string,
  name: string,
  file: File,
): Promise<TechnicalSource> {
  const payload = new FormData();
  payload.set("name", name);
  payload.set("file", file);
  return requestJson<TechnicalSource>(`/projects/${projectId}/sources/openapi`, {
    method: "POST",
    body: payload,
  });
}

export function archiveSource(sourceId: string): Promise<TechnicalSource> {
  return requestJson<TechnicalSource>(`/sources/${sourceId}/archive`, { method: "POST" });
}
