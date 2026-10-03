export type RequirementType = "BUSINESS" | "SYSTEM" | "NON_FUNCTIONAL" | "ACCEPTANCE";
export type RequirementStatus = "ACTIVE" | "RETIRED";
export type TraceTargetType = "FEATURE" | "EVIDENCE" | "DOCUMENT";
export type TraceRelation = "IMPLEMENTED_BY" | "VERIFIED_BY" | "DOCUMENTED_BY";

export interface TraceLink {
  id: string;
  target_type: TraceTargetType;
  relation: TraceRelation;
  target_reference: string;
  verified: boolean;
  created_by: string;
  created_at: string;
}

export interface Requirement {
  requirement_id: string;
  revision_id: string;
  project_id: string;
  key: string;
  revision: number;
  requirement_type: RequirementType;
  status: RequirementStatus;
  title: string;
  statement: string;
  owner: string;
  feature_id: string | null;
  acceptance_criteria: string[];
  changed_by: string;
  change_reason: string;
  created_at: string;
  trace_links: TraceLink[];
}

export interface RequirementCollection {
  items: Requirement[];
  total: number;
}

export interface TraceabilityCoverage {
  total_requirements: number;
  linked_to_feature: number;
  linked_to_evidence: number;
  linked_to_document: number;
  fully_traced: number;
  coverage_percent: number;
}

export interface CreateRequirementInput {
  key: string;
  requirement_type: RequirementType;
  title: string;
  statement: string;
  owner: string;
  feature_id: string | null;
  acceptance_criteria: string[];
  change_reason: string;
}
