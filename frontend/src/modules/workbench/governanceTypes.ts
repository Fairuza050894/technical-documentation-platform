export type DocumentationRequirement = "REQUIRED" | "SUPPLEMENTARY";
export type DocumentAvailability = "MISSING" | "AVAILABLE";
export type DocumentReadinessState = "NOT_READY" | "PARTIALLY_READY" | "READY";
export type ReadinessFindingSeverity = "BLOCKER" | "WARNING" | "ADVISORY";
export type ClaimClassification = "OBSERVED" | "INFERRED" | "UNVERIFIED";

export interface DocumentationChecklistItem {
  document_type: string;
  display_name: string;
  automation_profile: string;
  requirement: DocumentationRequirement;
  availability: DocumentAvailability;
  latest_document_id: string | null;
  latest_version_id: string | null;
  latest_version: string | null;
  latest_status: string | null;
}

export interface ProjectDocumentationChecklist {
  project_id: string;
  policy_key: string;
  registry_schema_version: string;
  items: DocumentationChecklistItem[];
  total: number;
  required_total: number;
  supplementary_total: number;
  available_total: number;
  missing_required_total: number;
}

export interface ReadinessFinding {
  rule_code: string;
  document_type: string;
  severity: ReadinessFindingSeverity;
  message: string;
  missing_input: string;
  remediation: string;
  supporting_references: string[];
}

export interface DocumentReadiness {
  project_id: string;
  policy_version: string;
  document_type: string;
  display_name: string;
  automation_profile: string;
  requirement: DocumentationRequirement;
  availability: DocumentAvailability;
  latest_status: string | null;
  readiness_state: DocumentReadinessState;
  eligible: boolean;
  findings: ReadinessFinding[];
  evidence_count: number;
  observed_claim_count: number;
  inferred_claim_count: number;
  unverified_claim_count: number;
}

export interface ProjectReadiness {
  project_id: string;
  project_status: string;
  policy_version: string;
  items: DocumentReadiness[];
  total: number;
  ready_total: number;
  partially_ready_total: number;
  not_ready_total: number;
  eligible_total: number;
  required_total: number;
  required_not_ready_total: number;
}

export interface EvidenceArtifact {
  id: string;
  workspace_id: string;
  project_id: string;
  feature_id: string | null;
  kind: string;
  source_system: string;
  source_reference: string;
  origin_id: string;
  checksum: string;
  content_reference: string;
  collection_method: string;
  collected_by: string;
  captured_at: string;
  created_at: string;
}

export interface EvidenceCollection {
  items: EvidenceArtifact[];
  total: number;
}

export interface GovernedClaim {
  id: string;
  workspace_id: string;
  project_id: string;
  feature_id: string | null;
  statement: string;
  classification: ClaimClassification;
  evidence_ids: string[];
  derivation_reference: string;
  relevant_document_types: string[];
  asserted_by: string;
  created_at: string;
}

export interface ClaimCollection {
  items: GovernedClaim[];
  total: number;
}

export interface ProjectDocumentationContext {
  checklist: ProjectDocumentationChecklist;
  readiness: ProjectReadiness;
  evidence: EvidenceArtifact[];
  claims: GovernedClaim[];
}
