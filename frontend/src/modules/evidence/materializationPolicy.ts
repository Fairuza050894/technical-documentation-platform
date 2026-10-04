import type { EvidenceKind } from "./types";

const MATERIALIZABLE_KINDS: ReadonlySet<EvidenceKind> = new Set([
  "USER_JOURNEY",
  "DEPLOYMENT_RUNTIME",
  "UAT_RESULT",
]);

export function isMaterializableEvidence(kind: EvidenceKind): boolean {
  return MATERIALIZABLE_KINDS.has(kind);
}
