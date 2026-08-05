import { useEffect, useState } from "react";

import { requestJson } from "../../shared/api/client";
import type { ApiState, HealthResponse } from "../types";

export function useHealthStatus(): ApiState {
  const [apiState, setApiState] = useState<ApiState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();

    async function loadHealth(): Promise<void> {
      try {
        const health = await requestJson<HealthResponse>("/health", {
          signal: controller.signal,
        });
        setApiState({ status: "available", health });
      } catch (error: unknown) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setApiState({ status: "unavailable" });
      }
    }

    void loadHealth();
    return () => controller.abort();
  }, []);

  return apiState;
}
