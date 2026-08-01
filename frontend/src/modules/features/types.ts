export type FeatureKind = "FEATURE" | "MODULE";
export type FeatureStatus = "ACTIVE" | "ARCHIVED";
export type DocumentationRequirement = "REQUIRED" | "OPTIONAL";
export type DocumentationCoverageStatus = "MISSING" | "PLANNED" | "AVAILABLE";

export interface FeatureCoverage {
  required_total: number;
  available_required: number;
  missing_required: number;
  optional_total: number;
}

export interface Feature {
  id: string;
  project_id: string;
  key: string;
  name: string;
  description: string;
  kind: FeatureKind;
  owner: string;
  status: FeatureStatus;
  documentation_coverage: FeatureCoverage;
  created_at: string;
  updated_at: string;
}

export interface FeatureCollection {
  items: Feature[];
  total: number;
}

export interface CreateFeatureInput {
  key: string;
  name: string;
  description: string;
  kind: FeatureKind;
  owner: string;
}

export interface DocumentationMapItem {
  document_type: string;
  requirement: DocumentationRequirement;
  coverage_status: DocumentationCoverageStatus;
  document_id: string | null;
  policy_key: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentationMap {
  feature_id: string;
  policy_key: string;
  items: DocumentationMapItem[];
  total: number;
}
