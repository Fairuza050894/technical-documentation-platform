
import { requestJson } from "../api/client";
import type { CurrentIdentity } from "./types";

export function getCurrentIdentity(signal?: AbortSignal): Promise<CurrentIdentity> {
  return requestJson<CurrentIdentity>("/identity/me", { signal });
}
