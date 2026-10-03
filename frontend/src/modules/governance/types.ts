export type RequirementType = "BUSINESS" | "SYSTEM" | "NON_FUNCTIONAL";
export type RequirementStatus = "DRAFT" | "ACTIVE" | "RETIRED";
export type TraceTargetType = "FEATURE" | "EVIDENCE" | "TEST" | "DOCUMENT" | "RELEASE" | "SOURCE";
export type ChangeSurface = "API" | "SCHEMA" | "REPOSITORY" | "TEST" | "DEPLOYMENT" | "RUNTIME";
export type WorkflowState =
  | "OPEN"
  | "ANALYSIS"
  | "UPDATE_REQUIRED"
  | "IN_REVIEW"
  | "APPROVED"
  | "RELEASED"
  | "REJECTED";

export interface RequirementRevision {
  id: string;
  requirement_id: string;
  project_id: string;
  revision: number;
  requirement_type: RequirementType;
  status: RequirementStatus;
  title: string;
  statement: string;
  rationale: string;
  created_by: string;
  created_at: string;
}

export interface TraceLink {
  id: string;
  project_id: string;
  requirement_id: string;
  target_type: TraceTargetType;
  target_id: string;
  relation: string;
  created_by: string;
  created_at: string;
}

export interface ImpactAssessment {
  id: string;
  project_id: string;
  change_reference: string;
  surface: ChangeSurface;
  affected_targets: string[];
  requires_action: boolean;
  assessed_by: string;
  assessed_at: string;
}

export interface WorkflowCase {
  id: string;
  project_id: string;
  impact_assessment_id: string;
  owner: string;
  state: WorkflowState;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface GovernanceSummary {
  requirements: RequirementRevision[];
  trace_links: TraceLink[];
  requirement_total: number;
  linked_requirement_total: number;
  coverage_percent: number;
  links_by_target: Record<string, number>;
  impact_assessments: ImpactAssessment[];
  workflow_cases: WorkflowCase[];
  impact_total: number;
  open_workflow_total: number;
}
