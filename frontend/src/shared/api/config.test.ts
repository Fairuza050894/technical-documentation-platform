
import { describe, expect, it } from "vitest";

import { API_BASE_URL, apiUrl, resolveApiBaseUrl } from "./config";

describe("API configuration", () => {
  it("uses a same-origin API path when no environment override is provided", () => {
    expect(resolveApiBaseUrl(undefined)).toBe("/api");
    expect(apiUrl("/health")).toBe(`${API_BASE_URL}/health`);
  });

  it("normalizes root-relative and absolute URLs", () => {
    expect(resolveApiBaseUrl("/gateway/api/")).toBe("/gateway/api");
    expect(resolveApiBaseUrl("https://docs.example.com/api/")).toBe(
      "https://docs.example.com/api",
    );
  });

  it("rejects unsupported URL schemes", () => {
    expect(() => resolveApiBaseUrl("file:///tmp/api")).toThrow(/HTTP or HTTPS/);
  });
});
