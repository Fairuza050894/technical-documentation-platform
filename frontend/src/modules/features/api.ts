import { requestJson } from "../../shared/api/client";
import type {
  CreateFeatureInput,
  DocumentationMap,
  Feature,
  FeatureCollection,
} from "./types";

function featureBasePath(workspaceId: string, projectId: string): string {
  return `/workspaces/${encodeURIComponent(workspaceId)}/projects/${encodeURIComponent(projectId)}/features`;
}

export function listFeatures(
  workspaceId: string,
  projectId: string,
  signal?: AbortSignal,
): Promise<FeatureCollection> {
  return requestJson<FeatureCollection>(featureBasePath(workspaceId, projectId), { signal });
}

export function createFeature(
  workspaceId: string,
  projectId: string,
  input: CreateFeatureInput,
): Promise<Feature> {
  return requestJson<Feature>(featureBasePath(workspaceId, projectId), {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function archiveFeature(
  workspaceId: string,
  projectId: string,
  featureId: string,
): Promise<Feature> {
  return requestJson<Feature>(
    `${featureBasePath(workspaceId, projectId)}/${encodeURIComponent(featureId)}/archive`,
    { method: "POST" },
  );
}

export function getDocumentationMap(
  workspaceId: string,
  projectId: string,
  featureId: string,
  signal?: AbortSignal,
): Promise<DocumentationMap> {
  return requestJson<DocumentationMap>(
    `${featureBasePath(workspaceId, projectId)}/${encodeURIComponent(featureId)}/documentation-map`,
    { signal },
  );
}
