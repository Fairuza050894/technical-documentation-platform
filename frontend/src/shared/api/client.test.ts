import { afterEach, describe, expect, it, vi } from "vitest";

import { requestJson } from "./client";

describe("requestJson", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns undefined for 204 responses without attempting JSON parsing", async () => {
    const json = vi.fn();
    const response = {
      ok: true,
      status: 204,
      json,
    } as unknown as Response;
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));

    await expect(requestJson<void>("/health")).resolves.toBeUndefined();
    expect(json).not.toHaveBeenCalled();
  });
});
