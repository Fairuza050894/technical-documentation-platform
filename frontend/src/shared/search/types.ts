export type SearchResultKind =
  | "source"
  | "document"
  | "evidence"
  | "claim"
  | "feature";

export interface SearchResult {
  kind: SearchResultKind;
  id: string;
  title: string;
  subtitle: string;
  projectId: string;
  route: {
    stage: string;
    featureId?: string;
  };
}

export interface SearchResultGroup {
  kind: SearchResultKind;
  label: string;
  items: SearchResult[];
}

export interface GlobalSearchResponse {
  query: string;
  groups: SearchResultGroup[];
  total: number;
}
