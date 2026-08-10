import { requestJson } from "../../shared/api/client";
import type {
  ClaimCollection,
  EvidenceCollection,
  ProjectDocumentationChecklist,
  ProjectDocumentationContext,
  ProjectReadiness,
} from "./governanceTypes";

export async function getProjectDocumentationContext(
  projectId: string,
): Promise<ProjectDocumentationContext> {
  const projectPath = `/projects/${encodeURIComponent(projectId)}`;
  const [checklist, readiness, evidenceCollection, claimCollection] = await Promise.all([
    requestJson<ProjectDocumentationChecklist>(`${projectPath}/documentation-checklist`),
    requestJson<ProjectReadiness>(`${projectPath}/readiness`),
    requestJson<EvidenceCollection>(`${projectPath}/evidence`),
    requestJson<ClaimCollection>(`${projectPath}/claims`),
  ]);

  return {
    checklist,
    readiness,
    evidence: evidenceCollection.items,
    claims: claimCollection.items,
  };
}
