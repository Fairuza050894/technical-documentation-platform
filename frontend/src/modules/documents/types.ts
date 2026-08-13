export type DocumentStatus =
  | "DRAFT"
  | "IN_REVIEW"
  | "CHANGES_REQUESTED"
  | "APPROVED"
  | "SUPERSEDED";

export type DocumentSectionChangeKind = "ADDED" | "MODIFIED" | "REMOVED";

export type GeneratedDocumentType =
  | "TECHNICAL_SOURCE_OVERVIEW"
  | "HLD"
  | "LLD"
  | "AS_BUILT";

export interface DocumentProvenanceReference {
  kind: "SOURCE_REGISTRY" | "CATALOG_SYNCHRONIZATION" | "EVIDENCE_ARTIFACT";
  reference: string;
  evidence_kind: string | null;
  checksum: string | null;
}

export interface GeneratedDocumentSummary {
  id: string;
  document_id: string;
  project_id: string;
  source_id: string | null;
  target_run_id: string | null;
  provenance?: DocumentProvenanceReference[];
  baseline_run_id: string | null;
  document_type: GeneratedDocumentType;
  document_format: "MARKDOWN";
  version: string;
  status: DocumentStatus;
  title: string;
  file_name: string;
  checksum: string;
  operation_count: number;
  schema_count: number;
  breaking_change_count: number;
  revision_reason: string;
  created_by: string;
  generated_at: string;
  updated_at: string;
  submitted_at: string | null;
  approved_at: string | null;
  superseded_at: string | null;
}

export interface GeneratedDocumentDetail extends GeneratedDocumentSummary {
  content: string;
  reused_existing_version: boolean;
}

export interface GeneratedDocumentCollection {
  items: GeneratedDocumentSummary[];
  total: number;
}

export interface WorkflowEvent {
  id: string;
  version_id: string;
  actor: string;
  action: string;
  previous_status: DocumentStatus | null;
  new_status: DocumentStatus;
  comment: string;
  created_at: string;
}

export interface WorkflowEventCollection {
  items: WorkflowEvent[];
  total: number;
}

export interface DocumentSectionChange {
  section_key: string;
  section_title: string;
  kind: DocumentSectionChangeKind;
  before_checksum: string;
  after_checksum: string;
  before_excerpt: string;
  after_excerpt: string;
}

export interface DocumentVersionComparison {
  baseline_version_id: string;
  target_version_id: string;
  document_id: string;
  total: number;
  added_total: number;
  modified_total: number;
  removed_total: number;
  changes: DocumentSectionChange[];
}
