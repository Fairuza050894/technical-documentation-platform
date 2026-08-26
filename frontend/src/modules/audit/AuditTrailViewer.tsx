import { useCallback, useEffect, useState } from "react";

import { Icon } from "../../shared/ui/Icon";
import { fetchAuditLogs } from "./api";
import type { AuditFilters, AuditLogEntry, AuditPagination } from "./types";

const ACTION_OPTIONS = [
  "CREATE",
  "UPDATE",
  "DELETE",
  "LOGIN",
  "LOGOUT",
  "EXPORT",
  "IMPORT",
  "APPROVE",
  "REJECT",
];

const INITIAL_FILTERS: AuditFilters = {
  page: 1,
  pageSize: 25,
  sortBy: "timestamp",
  sortOrder: "desc",
  actorId: "",
  action: "",
  resourceType: "",
  search: "",
  startDate: "",
  endDate: "",
};

function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function actionBadgeClass(action: string): string {
  if (action.includes("DELETE") || action.includes("REVOKE")) return "badge--danger";
  if (action.includes("CREATE") || action.includes("APPROVE")) return "badge--success";
  if (action.includes("UPDATE") || action.includes("IMPORT")) return "badge--info";
  if (action.includes("LOGIN")) return "badge--neutral";
  return "badge--default";
}

export function AuditTrailViewer() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [pagination, setPagination] = useState<AuditPagination | null>(null);
  const [filters, setFilters] = useState<AuditFilters>(INITIAL_FILTERS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadLogs = useCallback(async (currentFilters: AuditFilters) => {
    setLoading(true);
    setError("");
    try {
      const response = await fetchAuditLogs(currentFilters);
      setLogs(response.data.logs);
      setPagination(response.data.pagination);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void loadLogs(filters);
    return () => controller.abort();
  }, [filters, loadLogs]);

  const updateFilter = <K extends keyof AuditFilters>(
    key: K,
    value: AuditFilters[K],
  ): void => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
  };

  const goToPage = (page: number): void => {
    setFilters((prev) => ({ ...prev, page }));
  };

  const toggleSort = (field: string): void => {
    setFilters((prev) => ({
      ...prev,
      sortBy: field,
      sortOrder:
        prev.sortBy === field && prev.sortOrder === "desc" ? "asc" : "desc",
    }));
  };

  const clearFilters = (): void => {
    setFilters(INITIAL_FILTERS);
  };

  const hasActiveFilters =
    filters.actorId ||
    filters.action ||
    filters.resourceType ||
    filters.search ||
    filters.startDate ||
    filters.endDate;

  return (
    <div className="audit-viewer">
      <div className="audit-viewer__header">
        <div className="audit-viewer__title">
          <Icon name="server" size={20} />
          <h2>Audit Trail</h2>
          {pagination && (
            <span className="audit-viewer__count">
              {pagination.total.toLocaleString()} events
            </span>
          )}
        </div>
      </div>

      {/* ── Filters ── */}
      <div className="audit-viewer__filters">
        <div className="audit-filter-row">
          <label className="audit-filter">
            <span>Search</span>
            <input
              type="text"
              placeholder="Search actor, resource, request…"
              value={filters.search}
              onChange={(e) => updateFilter("search", e.target.value)}
            />
          </label>

          <label className="audit-filter">
            <span>Action</span>
            <select
              value={filters.action}
              onChange={(e) => updateFilter("action", e.target.value)}
            >
              <option value="">All actions</option>
              {ACTION_OPTIONS.map((action) => (
                <option key={action} value={action}>
                  {action}
                </option>
              ))}
            </select>
          </label>

          <label className="audit-filter">
            <span>Resource</span>
            <input
              type="text"
              placeholder="e.g. Document, Source"
              value={filters.resourceType}
              onChange={(e) => updateFilter("resourceType", e.target.value)}
            />
          </label>

          <label className="audit-filter">
            <span>From</span>
            <input
              type="date"
              value={filters.startDate}
              onChange={(e) => updateFilter("startDate", e.target.value)}
            />
          </label>

          <label className="audit-filter">
            <span>To</span>
            <input
              type="date"
              value={filters.endDate}
              onChange={(e) => updateFilter("endDate", e.target.value)}
            />
          </label>

          {hasActiveFilters && (
            <button
              type="button"
              className="audit-filter-clear"
              onClick={clearFilters}
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* ── Error ── */}
      {error && (
        <div className="audit-viewer__error" role="alert">
          {error}
        </div>
      )}

      {/* ── Table ── */}
      <div className="audit-viewer__table-wrap">
        <table className="audit-table">
          <thead>
            <tr>
              <th>
                <button type="button" onClick={() => toggleSort("timestamp")}>
                  Timestamp
                  {filters.sortBy === "timestamp" && (
                    <span>{filters.sortOrder === "desc" ? " ↓" : " ↑"}</span>
                  )}
                </button>
              </th>
              <th>Actor</th>
              <th>
                <button type="button" onClick={() => toggleSort("action")}>
                  Action
                  {filters.sortBy === "action" && (
                    <span>{filters.sortOrder === "desc" ? " ↓" : " ↑"}</span>
                  )}
                </button>
              </th>
              <th>Resource</th>
              <th>Request ID</th>
              <th>
                <button type="button" onClick={() => toggleSort("success")}>
                  Status
                  {filters.sortBy === "success" && (
                    <span>{filters.sortOrder === "desc" ? " ↓" : " ↑"}</span>
                  )}
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={6} className="audit-table__loading">
                  <span className="loading-bar" aria-hidden="true" />
                  Loading audit events…
                </td>
              </tr>
            )}

            {!loading && logs.length === 0 && (
              <tr>
                <td colSpan={6} className="audit-table__empty">
                  No audit events found
                  {hasActiveFilters && " matching your filters"}
                </td>
              </tr>
            )}

            {!loading &&
              logs.map((log) => (
                <tr key={log.id}>
                  <td className="audit-table__timestamp">
                    {formatTimestamp(log.timestamp)}
                  </td>
                  <td>
                    <span className="audit-table__actor">
                      {log.actor_display_name || log.actor_id}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${actionBadgeClass(log.action)}`}>
                      {log.action}
                    </span>
                  </td>
                  <td>
                    <span className="audit-table__resource">
                      {log.resource_type}
                      {log.resource_id && (
                        <small>/{log.resource_id.slice(0, 8)}</small>
                      )}
                    </span>
                  </td>
                  <td className="audit-table__request-id">
                    {log.request_id ? (
                      <code>{log.request_id.slice(0, 8)}</code>
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                  </td>
                  <td>
                    <span
                      className={`badge ${log.success ? "badge--success" : "badge--danger"}`}
                    >
                      {log.success ? "OK" : "FAIL"}
                    </span>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* ── Pagination ── */}
      {pagination && pagination.total_pages > 1 && (
        <div className="audit-viewer__pagination">
          <button
            type="button"
            disabled={pagination.page <= 1}
            onClick={() => goToPage(pagination.page - 1)}
          >
            Previous
          </button>
          <span className="audit-viewer__page-info">
            Page {pagination.page} of {pagination.total_pages}
          </span>
          <button
            type="button"
            disabled={pagination.page >= pagination.total_pages}
            onClick={() => goToPage(pagination.page + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}