export type ChangeKind = "ADDED" | "MODIFIED" | "REMOVED";
export type ChangeSeverity = "NON_BREAKING" | "POTENTIALLY_BREAKING" | "BREAKING";

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

export interface ImpactItem {
  document_type: string;
  action: "UPDATE_REQUIRED" | "REVIEW_REQUIRED" | "APPROVAL_REQUIRED";
  priority: "P0" | "P1" | "P2" | "P3";
  reason: string;
  source_changes: string[];
}

export interface ImpactAssessment {
  project_id: string;
  baseline_run_id: string;
  target_run_id: string;
  policy_key: string;
  approval_required: boolean;
  requirement_revalidation_required: boolean;
  highest_priority: "P0" | "P1" | "P2" | "P3";
  items: ImpactItem[];
}
