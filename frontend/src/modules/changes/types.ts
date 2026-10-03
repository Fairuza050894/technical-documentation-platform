export type ChangeKind = "ADDED" | "MODIFIED" | "REMOVED";
export type ChangeSeverity = "NON_BREAKING" | "POTENTIALLY_BREAKING" | "BREAKING";
export type ImpactLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface ChangeItem {
  entity_type: "OPERATION" | "SCHEMA";
  entity_key: string;
  kind: ChangeKind;
  severity: ChangeSeverity;
  summary: string;
  before_pointer: string;
  after_pointer: string;
  details: Record<string, unknown>;
}

export interface ComparisonResult {
  project_id: string;
  baseline_run_id: string;
  target_run_id: string;
  total: number;
  breaking_total: number;
  changes: ChangeItem[];
}

export interface ChangeImpactItem {
  entity_type: string;
  entity_key: string;
  level: ImpactLevel;
  required_document_types: string[];
  requirement_review_required: boolean;
  test_execution_required: boolean;
  rationale: string[];
}

export interface ImpactAssessment {
  project_id: string;
  baseline_run_id: string;
  target_run_id: string;
  level: ImpactLevel;
  required_document_types: string[];
  requirement_review_required: boolean;
  test_execution_required: boolean;
  impacts: ChangeImpactItem[];
}
