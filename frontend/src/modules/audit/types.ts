export interface AuditLogEntry {
  id: number;
  event_id: string;
  timestamp: string;
  actor_id: string;
  actor_display_name: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  workspace_id: string | null;
  project_id: string | null;
  request_id: string | null;
  ip_address: string;
  success: boolean;
  error_message: string | null;
  metadata: Record<string, unknown> | null;
}

export interface AuditPagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface AuditLogResponse {
  success: boolean;
  data: {
    logs: AuditLogEntry[];
    pagination: AuditPagination;
  };
}

export interface AuditStatsResponse {
  success: boolean;
  data: {
    by_action: Array<{ action: string; count: number }>;
    by_resource: Array<{ resource_type: string; count: number }>;
    by_outcome: Array<{ success: number; count: number }>;
    daily_activity: Array<{ date: string; count: number }>;
    top_actors: Array<{
      actor_id: string;
      actor_display_name: string;
      count: number;
      last_activity: string;
    }>;
  };
}

export interface AuditFilters {
  page: number;
  pageSize: number;
  sortBy: string;
  sortOrder: "asc" | "desc";
  actorId: string;
  action: string;
  resourceType: string;
  search: string;
  startDate: string;
  endDate: string;
}