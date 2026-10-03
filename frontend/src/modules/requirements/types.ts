export type RequirementType =
  | "BUSINESS"
  | "SYSTEM"
  | "FUNCTIONAL"
  | "NON_FUNCTIONAL"
  | "COMPLIANCE";

export type RequirementStatus = "DRAFT" | "APPROVED" | "RETIRED";

export interface Requirement {
  id: string;
  workspace_id: string;
  project_id: string;
  key: string;
  requirement_type: RequirementType;
  title: string;
  statement: string;
  acceptance_criteria: string[];
  rationale: string;
  feature_id: string | null;
  status: RequirementStatus;
  revision: number;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface RequirementCollection {
  items: Requirement[];
  total: number;
}

export interface TraceabilityCoverage {
  feature: boolean;
  evidence: boolean;
  document: boolean;
  test: boolean;
  change: boolean;
}

export interface TraceabilityLink {
  id: string;
  requirement_id: string;
  target_type: "FEATURE" | "EVIDENCE" | "DOCUMENT" | "TEST" | "CHANGE";
  target_id: string;
  relation:
    | "IMPLEMENTED_BY"
    | "SUPPORTED_BY"
    | "DOCUMENTED_BY"
    | "VERIFIED_BY"
    | "AFFECTED_BY";
  created_by: string;
  created_at: string;
}

export interface TraceabilityRecord {
  requirement: Requirement;
  links: TraceabilityLink[];
  coverage: TraceabilityCoverage;
}

export interface ProjectTraceability {
  items: TraceabilityRecord[];
  total: number;
}

export type WorkflowState =
  | "OPEN"
  | "TRIAGED"
  | "IN_PROGRESS"
  | "IN_REVIEW"
  | "APPROVED"
  | "CLOSED"
  | "CANCELLED";

export interface WorkflowItem {
  id: string;
  workspace_id: string;
  project_id: string;
  entity_type: "REQUIREMENT" | "DOCUMENT" | "CHANGE_IMPACT";
  entity_id: string;
  title: string;
  priority: "P0" | "P1" | "P2" | "P3";
  state: WorkflowState;
  assignee: string;
  created_by: string;
  due_at: string;
  created_at: string;
  updated_at: string;
  overdue: boolean;
}

export interface WorkflowCollection {
  items: WorkflowItem[];
  total: number;
}
