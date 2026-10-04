import { describe, expect, it } from "vitest";

import { isMaterializableEvidence } from "./EvidenceMaterializationPanel";

describe("evidence materialization boundary", () => {
  it.each(["USER_JOURNEY", "DEPLOYMENT_RUNTIME", "UAT_RESULT"] as const)(
    "allows typed semantic evidence %s",
    (kind) => {
      expect(isMaterializableEvidence(kind)).toBe(true);
    },
  );

  it.each(["SOURCE_ARTIFACT", "CATALOG_SNAPSHOT"] as const)(
    "does not offer semantic materialization for canonical %s evidence",
    (kind) => {
      expect(isMaterializableEvidence(kind)).toBe(false);
    },
  );
});
