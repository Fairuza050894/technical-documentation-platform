import { listGeneratedDocuments } from "../../modules/documents/api";
import { listProjectClaims, listProjectEvidence } from "../../modules/evidence/api";
import { listFeatures } from "../../modules/features/api";
import { listProjects } from "../../modules/projects/api";
import { listSources } from "../../modules/sources/api";
import type {
  GlobalSearchResponse,
  SearchResult,
  SearchResultGroup,
  SearchResultKind,
} from "./types";

const MAX_RESULTS_PER_GROUP = 5;

export async function executeGlobalSearch(
  query: string,
  workspaceId: string | null,
  signal?: AbortSignal,
): Promise<GlobalSearchResponse> {
  const normalizedQuery = query.trim().toLowerCase();
  if (normalizedQuery.length < 2) {
    return { query, groups: [], total: 0 };
  }

  const projectCollection = await listProjects(signal);
  const activeProjects = projectCollection.items.filter(
    (project) => project.status === "ACTIVE",
  );

  const allResults: Record<SearchResultKind, SearchResult[]> = {
    source: [],
    document: [],
    evidence: [],
    claim: [],
    feature: [],
  };

  const searchTasks = activeProjects.flatMap((project) => [
    searchSources(project.id, normalizedQuery, signal).then(
      (results) => { allResults.source.push(...results); },
      () => { /* ignore individual project errors */ },
    ),
    searchDocuments(project.id, normalizedQuery, signal).then(
      (results) => { allResults.document.push(...results); },
      () => { /* ignore */ },
    ),
    searchEvidence(project.id, normalizedQuery, signal).then(
      (results) => { allResults.evidence.push(...results); },
      () => { /* ignore */ },
    ),
    searchClaims(project.id, normalizedQuery, signal).then(
      (results) => { allResults.claim.push(...results); },
      () => { /* ignore */ },
    ),
    searchFeatures(project.id, workspaceId, normalizedQuery, signal).then(
      (results) => { allResults.feature.push(...results); },
      () => { /* ignore */ },
    ),
  ]);

  await Promise.allSettled(searchTasks);

  const groups: SearchResultGroup[] = [];
  const kindLabels: Record<SearchResultKind, string> = {
    source: "Sources",
    document: "Documents",
    evidence: "Evidence",
    claim: "Claims",
    feature: "Features",
  };

  let total = 0;
  for (const kind of [
    "feature",
    "source",
    "document",
    "evidence",
    "claim",
  ] as SearchResultKind[]) {
    const items = allResults[kind].slice(0, MAX_RESULTS_PER_GROUP);
    if (items.length > 0) {
      groups.push({ kind, label: kindLabels[kind], items });
      total += items.length;
    }
  }

  return { query, groups, total };
}

async function searchSources(
  projectId: string,
  query: string,
  signal?: AbortSignal,
): Promise<SearchResult[]> {
  const collection = await listSources(projectId, signal);
  return collection.items
    .filter(
      (source) =>
        source.name.toLowerCase().includes(query) ||
        source.original_file_name.toLowerCase().includes(query) ||
        source.api_title.toLowerCase().includes(query),
    )
    .map((source) => ({
      kind: "source" as const,
      id: source.id,
      title: source.name,
      subtitle: `${source.original_file_name} · ${source.status}`,
      projectId,
      route: { stage: "sources" },
    }));
}

async function searchDocuments(
  projectId: string,
  query: string,
  signal?: AbortSignal,
): Promise<SearchResult[]> {
  const collection = await listGeneratedDocuments(projectId, signal);
  return collection.items
    .filter(
      (document) =>
        document.title.toLowerCase().includes(query) ||
        document.file_name.toLowerCase().includes(query) ||
        document.status.toLowerCase().includes(query) ||
        document.created_by.toLowerCase().includes(query),
    )
    .map((document) => ({
      kind: "document" as const,
      id: document.id,
      title: document.title,
      subtitle: `v${document.version} · ${document.status}`,
      projectId,
      route: { stage: "documents" },
    }));
}

async function searchEvidence(
  projectId: string,
  query: string,
  signal?: AbortSignal,
): Promise<SearchResult[]> {
  const collection = await listProjectEvidence(projectId, signal);
  return collection.items
    .filter(
      (artifact) =>
        artifact.kind.toLowerCase().includes(query) ||
        artifact.source_reference.toLowerCase().includes(query) ||
        artifact.origin_id.toLowerCase().includes(query) ||
        artifact.content_reference.toLowerCase().includes(query),
    )
    .map((artifact) => ({
      kind: "evidence" as const,
      id: artifact.id,
      title: formatKind(artifact.kind),
      subtitle: `${artifact.origin_id} · ${artifact.source_system}`,
      projectId,
      route: { stage: "evidence" },
    }));
}

async function searchClaims(
  projectId: string,
  query: string,
  signal?: AbortSignal,
): Promise<SearchResult[]> {
  const collection = await listProjectClaims(projectId, signal);
  return collection.items
    .filter(
      (claim) =>
        claim.statement.toLowerCase().includes(query) ||
        claim.classification.toLowerCase().includes(query) ||
        claim.asserted_by.toLowerCase().includes(query),
    )
    .map((claim) => ({
      kind: "claim" as const,
      id: claim.id,
      title: claim.statement.length > 60 ? `${claim.statement.slice(0, 60)}...` : claim.statement,
      subtitle: `${claim.classification} · ${claim.evidence_ids.length} evidence`,
      projectId,
      route: { stage: "evidence" },
    }));
}

async function searchFeatures(
  projectId: string,
  workspaceId: string | null,
  query: string,
  signal?: AbortSignal,
): Promise<SearchResult[]> {
  if (!workspaceId) return [];
  const collection = await listFeatures(workspaceId, projectId, signal);
  return collection.items
    .filter(
      (feature) =>
        feature.name.toLowerCase().includes(query) ||
        feature.key.toLowerCase().includes(query) ||
        feature.description.toLowerCase().includes(query) ||
        feature.kind.toLowerCase().includes(query) ||
        (feature.owner ?? "").toLowerCase().includes(query),
    )
    .map((feature) => ({
      kind: "feature" as const,
      id: feature.id,
      title: feature.name,
      subtitle: `${feature.key} · ${feature.kind} · ${feature.status}`,
      projectId,
      route: { stage: "features", featureId: feature.id },
    }));
}

function formatKind(kind: string): string {
  return kind
    .toLowerCase()
    .split("_")
    .map((part: string) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
