export type EvidenceKind =
  | "SOURCE_ARTIFACT"
  | "CATALOG_SNAPSHOT"
  | "USER_JOURNEY"
  | "DEPLOYMENT_RUNTIME"
  | "UAT_RESULT";

export type EvidenceSourceSystem =
  | "SOURCE_REGISTRY"
  | "API_CATALOG"
  | "GOVERNED_REFERENCE";

export type EvidenceCollectionMethod =
  | "SOURCE_IMPORT"
  | "DETERMINISTIC_NORMALIZATION"
  | "REFERENCE_REGISTRATION";

export type ClaimClassification = "OBSERVED" | "INFERRED" | "UNVERIFIED";

export interface EvidenceArtifact {
  id: string;
  workspace_id: string;
  project_id: string;
  feature_id: string | null;
  kind: EvidenceKind;
  source_system: EvidenceSourceSystem;
  source_reference: string;
  origin_id: string;
  checksum: string;
  content_reference: string;
  collection_method: EvidenceCollectionMethod;
  collected_by: string;
  captured_at: string;
  created_at: string;
}

export interface EvidenceCollection {
  items: EvidenceArtifact[];
  total: number;
}

export interface EvidenceMaterialization {
  evidence_id: string;
  project_id: string;
  kind: string;
  schema_version: string;
  checksum: string;
  materialized_by: string;
  materialized_at: string;
}

export interface Claim {
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
  items: Claim[];
  total: number;
}

export interface RegisterReferencedEvidenceInput {
  kind: "USER_JOURNEY" | "DEPLOYMENT_RUNTIME" | "UAT_RESULT";
  source_reference: string;
  origin_id: string;
  checksum: string;
  content_reference: string;
  captured_at: string;
  feature_id?: string;
}

export interface CreateClaimInput {
  statement: string;
  classification: ClaimClassification;
  evidence_ids?: string[];
  derivation_reference?: string;
  relevant_document_types?: string[];
  feature_id?: string;
}
