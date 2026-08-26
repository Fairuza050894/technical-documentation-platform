"""Audit log query API router.

Endpoints:
  GET /api/audit-logs          — list with filters & pagination
  GET /api/audit-logs/stats    — aggregate statistics
  GET /api/audit-logs/export   — CSV export
  GET /api/audit-logs/{id}     — single log detail
"""

from __future__ import annotations

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from tdp.audit.store import AuditStore

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


def _get_store(request: Request) -> AuditStore:
    return request.app.state.audit_store


@router.get("")
async def list_audit_logs(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    sort_by: str = Query("timestamp", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    actor_id: str | None = Query(None, description="Filter by actor ID"),
    action: str | None = Query(None, description="Filter by action (comma-separated)"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    resource_id: str | None = Query(None, description="Filter by resource ID"),
    workspace_id: str | None = Query(None, description="Filter by workspace"),
    project_id: str | None = Query(None, description="Filter by project"),
    success: bool | None = Query(None, description="Filter by success/failure"),
    request_id: str | None = Query(None, description="Filter by request ID"),
    start_date: str | None = Query(None, description="Start date (ISO format)"),
    end_date: str | None = Query(None, description="End date (ISO format)"),
    search: str | None = Query(None, description="Full-text search"),
    store: AuditStore = Depends(_get_store),
):
    """List audit logs with filtering, pagination, and sorting."""
    actions = [a.strip() for a in action.split(",")] if action else None
    result = store.query(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        actor_id=actor_id,
        actions=actions,
        resource_type=resource_type,
        resource_id=resource_id,
        workspace_id=workspace_id,
        project_id=project_id,
        success=success,
        request_id=request_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    return {"success": True, "data": result}


@router.get("/stats")
async def audit_log_stats(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    store: AuditStore = Depends(_get_store),
):
    """Aggregate statistics for audit logs."""
    result = store.stats(start_date=start_date, end_date=end_date)
    return {"success": True, "data": result}


@router.get("/export")
async def export_audit_logs(
    actor_id: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    workspace_id: str | None = None,
    project_id: str | None = None,
    success: bool | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    store: AuditStore = Depends(_get_store),
):
    """Export audit logs as CSV (max 10,000 rows)."""
    actions = [a.strip() for a in action.split(",")] if action else None
    result = store.query(
        page=1,
        page_size=10000,
        sort_by="timestamp",
        sort_order="desc",
        actor_id=actor_id,
        actions=actions,
        resource_type=resource_type,
        workspace_id=workspace_id,
        project_id=project_id,
        success=success,
        start_date=start_date,
        end_date=end_date,
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Event ID", "Timestamp", "Actor ID", "Actor Name",
        "Action", "Resource Type", "Resource ID", "Workspace ID",
        "Project ID", "Request ID", "IP Address", "Success",
        "Error Message", "Metadata",
    ])
    for log in result["logs"]:
        writer.writerow([
            log["id"], log["event_id"], log["timestamp"],
            log["actor_id"], log["actor_display_name"],
            log["action"], log["resource_type"], log["resource_id"],
            log["workspace_id"], log["project_id"],
            log["request_id"], log["ip_address"],
            log["success"], log["error_message"],
            str(log.get("metadata", "")),
        ])

    output.seek(0)
    filename = f"audit-logs-{datetime.now().strftime('%Y-%m-%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{log_id}")
async def get_audit_log(
    log_id: int,
    store: AuditStore = Depends(_get_store),
):
    """Get a single audit log by ID."""
    log = store.get_by_id(log_id)
    if not log:
        return {"success": False, "message": "Audit log not found"}
    return {"success": True, "data": log}