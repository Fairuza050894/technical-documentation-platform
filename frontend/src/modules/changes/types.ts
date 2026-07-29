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
