import { beforeEach, describe, expect, it, vi } from "vitest";

const requestJson = vi.fn();

vi.mock("../../shared/api/client", () => ({
  requestJson,
}));

import { getWebhookEvent } from "./api";

describe("scanner API client", () => {
  beforeEach(() => {
    requestJson.mockReset();
    requestJson.mockResolvedValue({});
  });

  it("interpolates and URL-encodes webhook event identifiers", async () => {
    await getWebhookEvent("event/with spaces");

    expect(requestJson).toHaveBeenCalledWith(
      "/scanner/webhooks/events/event%2Fwith%20spaces",
    );
  });
});
