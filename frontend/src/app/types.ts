import type { AppRoute } from "./router";

export interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
  environment: string;
}

export type ApiState =
  | { status: "loading" }
  | { status: "available"; health: HealthResponse }
  | { status: "unavailable" };

export type WorkspaceLoadState = "loading" | "ready" | "error";

export type Navigate = (route: AppRoute, replace?: boolean) => void;
