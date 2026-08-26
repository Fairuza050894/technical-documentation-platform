import { requestJson } from "../../shared/api/client";
import type { AuditFilters, AuditLogResponse, AuditStatsResponse } from "./types";

export function fetchAuditLogs(
  filters: Partial<AuditFilters>,
  signal?: AbortSignal,
): Promise<AuditLogResponse> {
  const params = new URLSearchParams();

  if (filters.page) params.set("page", String(filters.page));
  if (filters.pageSize) params.set("page_size", String(filters.pageSize));
  if (filters.sortBy) params.set("sort_by", filters.sortBy);
  if (filters.sortOrder) params.set("sort_order", filters.sortOrder);
  if (filters.actorId) params.set("actor_id", filters.actorId);
  if (filters.action) params.set("action", filters.action);
  if (filters.resourceType) params.set("resource_type", filters.resourceType);
  if (filters.search) params.set("search", filters.search);
  if (filters.startDate) params.set("start_date", filters.startDate);
  if (filters.endDate) params.set("end_date", filters.endDate);

  const query = params.toString();
  const path = `/audit-logs${query ? `?${query}` : ""}`;

  return requestJson<AuditLogResponse>(path, { signal });
}

export function fetchAuditStats(
  signal?: AbortSignal,
): Promise<AuditStatsResponse> {
  return requestJson<AuditStatsResponse>("/audit-logs/stats", { signal });
}