import { describe, expect, it } from "vitest";

import { isMaterializableEvidence } from "./EvidenceMaterializationPanel";

describe("evidence materialization boundary", () => {
  it("allows only typed semantic referenced evidence", () => {
    for (const kind of ["USER_JOURNEY", "DEPLOYMENT_RUNTIME", "UAT_RESULT"] as const) {
      expect(isMaterializableEvidence(kind)).toBe(true);
    }
  });

  it("does not offer semantic materialization for canonical source evidence", () => {
    for (const kind of ["SOURCE_ARTIFACT", "CATALOG_SNAPSHOT"] as const) {
      expect(isMaterializableEvidence(kind)).toBe(false);
    }
  });
});
