import { beforeEach, describe, expect, it, vi } from "vitest";

const { requestJson } = vi.hoisted(() => ({
  requestJson: vi.fn(),
}));

vi.mock("../../shared/api/client", () => ({
  requestJson,
}));

import { addRequirementTraceLink } from "./api";

describe("requirements API client", () => {
  beforeEach(() => {
    requestJson.mockReset();
    requestJson.mockResolvedValue({});
  });

  it("derives governed relations from trace target type", async () => {
    const cases = [
      ["FEATURE", "IMPLEMENTED_BY"],
      ["EVIDENCE", "VERIFIED_BY"],
      ["DOCUMENT", "DOCUMENTED_BY"],
    ] as const;

    for (const [targetType, relation] of cases) {
      requestJson.mockClear();
      await addRequirementTraceLink(
        "workspace/1",
        "project/1",
        "requirement/1",
        targetType,
        "  target-id  ",
      );

      expect(requestJson).toHaveBeenCalledWith(
        "/workspaces/workspace%2F1/projects/project%2F1/requirements/requirement%2F1/trace-links",
        {
          method: "POST",
          body: JSON.stringify({
            target_type: targetType,
            relation,
            target_reference: "target-id",
          }),
        },
      );
    }
  });
});
