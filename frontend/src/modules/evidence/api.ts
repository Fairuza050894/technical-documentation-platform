import { requestJson } from "../../shared/api/client";
import type {
  Claim,
  ClaimCollection,
  CreateClaimInput,
  EvidenceArtifact,
  EvidenceCollection,
  EvidenceMaterialization,
  RegisterReferencedEvidenceInput,
} from "./types";

export function listProjectEvidence(
  projectId: string,
): Promise<EvidenceCollection> {
  return requestJson<EvidenceCollection>(`/projects/${projectId}/evidence`);
}

export function getEvidence(artifactId: string): Promise<EvidenceArtifact> {
  return requestJson<EvidenceArtifact>(`/evidence/${artifactId}`);
}

export function registerSourceEvidence(
  projectId: string,
  sourceId: string,
): Promise<EvidenceArtifact> {
  return requestJson<EvidenceArtifact>(
    `/projects/${projectId}/evidence/source-artifacts/${sourceId}`,
    { method: "POST" },
  );
}

export function registerSnapshotEvidence(
  projectId: string,
  synchronizationId: string,
): Promise<EvidenceArtifact> {
  return requestJson<EvidenceArtifact>(
    `/projects/${projectId}/evidence/catalog-snapshots/${synchronizationId}`,
    { method: "POST" },
  );
}

export function registerReferencedEvidence(
  projectId: string,
  input: RegisterReferencedEvidenceInput,
): Promise<EvidenceArtifact> {
  return requestJson<EvidenceArtifact>(
    `/projects/${projectId}/evidence/references`,
    { method: "POST", body: JSON.stringify(input) },
  );
}

export function materializeEvidence(
  projectId: string,
  artifactId: string,
  manifest: Record<string, unknown>,
): Promise<EvidenceMaterialization> {
  return requestJson<EvidenceMaterialization>(
    `/projects/${projectId}/evidence/${artifactId}/materialization`,
    { method: "POST", body: JSON.stringify({ manifest }) },
  );
}

export function getEvidenceMaterialization(
  artifactId: string,
): Promise<EvidenceMaterialization> {
  return requestJson<EvidenceMaterialization>(
    `/evidence/${artifactId}/materialization`,
  );
}

export function listProjectClaims(
  projectId: string,
): Promise<ClaimCollection> {
  return requestJson<ClaimCollection>(`/projects/${projectId}/claims`);
}

export function getClaim(claimId: string): Promise<Claim> {
  return requestJson<Claim>(`/claims/${claimId}`);
}

export function createClaim(
  projectId: string,
  input: CreateClaimInput,
): Promise<Claim> {
  return requestJson<Claim>(`/projects/${projectId}/claims`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}
