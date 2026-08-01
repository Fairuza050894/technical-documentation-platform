
const DEFAULT_API_BASE_URL = "/api";

export function resolveApiBaseUrl(value: string | undefined): string {
  const candidate = value?.trim() || DEFAULT_API_BASE_URL;
  const withoutTrailingSlash = candidate.replace(/\/+$/, "");

  if (withoutTrailingSlash.startsWith("/")) {
    return withoutTrailingSlash;
  }

  let parsed: URL;
  try {
    parsed = new URL(withoutTrailingSlash);
  } catch {
    throw new Error(
      "VITE_API_BASE_URL must be a root-relative path or an absolute HTTP(S) URL.",
    );
  }

  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error("VITE_API_BASE_URL must use HTTP or HTTPS.");
  }
  return withoutTrailingSlash;
}

const configuredApiBaseUrl: unknown = import.meta.env.VITE_API_BASE_URL;

export const API_BASE_URL = resolveApiBaseUrl(
  typeof configuredApiBaseUrl === "string" ? configuredApiBaseUrl : undefined,
);

export function apiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}
