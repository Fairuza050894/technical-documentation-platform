import { afterEach, describe, expect, it, vi } from "vitest";

import { getWebhookEvent } from "./api";

describe("scanner API", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("interpolates and URL-encodes webhook event identifiers", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: "event/42" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await getWebhookEvent("event/42");

    expect(fetchMock).toHaveBeenCalledOnce();
    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "/api/scanner/webhooks/events/event%2F42",
    );
  });
});
