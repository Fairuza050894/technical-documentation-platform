import { useEffect, useMemo, useState } from "react";

import { listSynchronizations } from "../catalog/api";
import type { SynchronizationRun } from "../catalog/types";
import { listGeneratedDocuments } from "../documents/api";
import type { GeneratedDocumentSummary } from "../documents/types";
import { listProjects } from "../projects/api";
import type { Project } from "../projects/types";
import { listSources } from "../sources/api";
import type { TechnicalSource } from "../sources/types";

export type OverviewNavigationTarget =
  | "Projects"
  | "Sources"
  | "API Catalog"
  | "Changes"
  | "Documents";

interface OperationalOverviewProps {
  serviceState: "loading" | "available" | "unavailable";
  serviceVersion: string | undefined;
  onNavigate: (target: OverviewNavigationTarget) => void;
}

interface OverviewData {
  projects: Project[];
  sources: TechnicalSource[];
  runs: SynchronizationRun[];
  documents: GeneratedDocumentSummary[];
}

interface ActivityItem {
  id: string;
  timestamp: string;
  action: string;
  context: string;
  result: string;
  tone: "success" | "warning" | "danger" | "neutral";
}

const EMPTY_DATA: OverviewData = {
  projects: [],
  sources: [],
  runs: [],
  documents: [],
};

export function OperationalOverview({
  serviceState,
  serviceVersion,
  onNavigate,
}: OperationalOverviewProps) {
  const [data, setData] = useState<OverviewData>(EMPTY_DATA);
  const [loadState, setLoadState] = useState<"loading" | "ready" | "error">("loading");
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadOverview(): Promise<void> {
      try {
        const projectCollection = await listProjects();
        const activeProjects = projectCollection.items.filter(
          (project) => project.status === "ACTIVE",
        );

        const sourceCollections = await Promise.all(
          activeProjects.map((project) => listSources(project.id)),
        );
        const sources = sourceCollections.flatMap((collection) => collection.items);

        const [runCollections, documentCollections] = await Promise.all([
          Promise.all(
            sources
              .filter((source) => source.status === "READY")
              .map((source) => listSynchronizations(source.id)),
          ),
          Promise.all(activeProjects.map((project) => listGeneratedDocuments(project.id))),
        ]);

        if (!active) {
          return;
        }

        setData({
          projects: activeProjects,
          sources,
          runs: runCollections.flatMap((collection) => collection.items),
          documents: documentCollections.flatMap((collection) => collection.items),
        });
        setLoadState("ready");
      } catch (error: unknown) {
        if (!active) {
          return;
        }
        setLoadError(
          error instanceof Error
            ? error.message
            : "Operational overview could not be loaded.",
        );
        setLoadState("error");
      }
    }

    void loadOverview();
    return () => {
      active = false;
    };
  }, []);

  const dashboard = useMemo(() => buildDashboard(data), [data]);

  return (
    <>
      <header className="topbar topbar--operational">
        <div>
          <p className="eyebrow">Operational workspace</p>
          <h1>Overview</h1>
          <p className="page-summary">
            Source-backed status across projects, technical sources, snapshots, and document
            reviews.
          </p>
        </div>
        <div className="page-actions" aria-label="Quick actions">
          <button
            type="button"
            className="button button--secondary"
            onClick={() => onNavigate("Sources")}
          >
            Import source
          </button>
          <button
            type="button"
            className="button button--primary"
            onClick={() => onNavigate("Documents")}
          >
            Generate document
          </button>
        </div>
      </header>

      {serviceState === "unavailable" && (
        <div className="notice notice--error" role="alert">
          <span>The backend API is offline. Operational data may be unavailable.</span>
          <code>make dev-backend</code>
        </div>
      )}

      {loadState === "loading" && (
        <div className="dashboard-loading" role="status">
          <span className="loading-bar" aria-hidden="true" />
          Loading operational data…
        </div>
      )}

      {loadState === "error" && (
        <div className="notice notice--error" role="alert">
          <span>{loadError}</span>
          <button
            type="button"
            className="button button--secondary"
            onClick={() => globalThis.location.reload()}
          >
            Reload
          </button>
        </div>
      )}

      {loadState === "ready" && (
        <>
          <section className="content-section" aria-labelledby="workspace-metrics-title">
            <div className="section-heading section-heading--split">
              <div>
                <h2 id="workspace-metrics-title">Workspace metrics</h2>
                <p>Current counts assembled from existing platform APIs.</p>
              </div>
              <span className="data-provenance">
                Live data {serviceVersion ? `· API v${serviceVersion}` : ""}
              </span>
            </div>

            <div className="metric-grid">
              <MetricCard
                label="Active projects"
                value={dashboard.activeProjects}
                detail="Project boundaries available for technical sources."
                onClick={() => onNavigate("Projects")}
              />
              <MetricCard
                label="Ready sources"
                value={dashboard.readySources}
                detail="Validated OpenAPI artifacts currently available."
                onClick={() => onNavigate("Sources")}
              />
              <MetricCard
                label="Completed snapshots"
                value={dashboard.completedSnapshots}
                detail="Successful deterministic synchronization runs."
                onClick={() => onNavigate("API Catalog")}
              />
              <MetricCard
                label="Pending reviews"
                value={dashboard.pendingReviews}
                detail="Versions in review or waiting for changes."
                tone={dashboard.pendingReviews > 0 ? "warning" : "neutral"}
                onClick={() => onNavigate("Documents")}
              />
            </div>
          </section>

          <div className="overview-layout">
            <section className="content-section overview-panel" aria-labelledby="attention-title">
              <div className="section-heading">
                <div>
                  <h2 id="attention-title">Attention required</h2>
                  <p>Conditions that may block publication or source accuracy.</p>
                </div>
              </div>

              {dashboard.attention.length === 0 ? (
                <div className="attention-clear">
                  <span className="service-dot service-dot--available" aria-hidden="true" />
                  <span>
                    <strong>No operational issues detected</strong>
                    <small>All available source-backed checks are clear.</small>
                  </span>
                </div>
              ) : (
                <ul className="attention-list">
                  {dashboard.attention.map((item) => (
                    <li key={item.label}>
                      <span className={`attention-severity attention-severity--${item.tone}`}>
                        {item.value}
                      </span>
                      <span>
                        <strong>{item.label}</strong>
                        <small>{item.detail}</small>
                      </span>
                      <button
                        type="button"
                        className="button button--quiet"
                        onClick={() => onNavigate(item.target)}
                      >
                        Review
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="content-section overview-panel" aria-labelledby="quick-actions-title">
              <div className="section-heading">
                <div>
                  <h2 id="quick-actions-title">Quick actions</h2>
                  <p>Continue the source-to-document workflow.</p>
                </div>
              </div>

              <div className="quick-action-list">
                <QuickAction
                  title="Manage projects"
                  detail="Create or archive project boundaries."
                  onClick={() => onNavigate("Projects")}
                />
                <QuickAction
                  title="Import OpenAPI"
                  detail="Register a JSON or YAML source artifact."
                  onClick={() => onNavigate("Sources")}
                />
                <QuickAction
                  title="Synchronize catalog"
                  detail="Create a normalized source snapshot."
                  onClick={() => onNavigate("API Catalog")}
                />
                <QuickAction
                  title="Review documents"
                  detail="Open lifecycle status and approval history."
                  onClick={() => onNavigate("Documents")}
                />
              </div>
            </section>
          </div>

          <section className="content-section" aria-labelledby="recent-activity-title">
            <div className="section-heading section-heading--split">
              <div>
                <h2 id="recent-activity-title">Recent activity</h2>
                <p>Latest synchronization and document lifecycle events.</p>
              </div>
              <span className="record-count">{dashboard.activities.length} activities</span>
            </div>

            {dashboard.activities.length === 0 ? (
              <div className="empty-state empty-state--compact">
                <h3>No activity yet</h3>
                <p>Import and synchronize a source to begin the traceable workflow.</p>
              </div>
            ) : (
              <div className="table-frame table-frame--dense">
                <table>
                  <caption className="visually-hidden">
                    Recent synchronization and document activities
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Time</th>
                      <th scope="col">Activity</th>
                      <th scope="col">Context</th>
                      <th scope="col">Result</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboard.activities.map((activity) => (
                      <tr key={activity.id}>
                        <td>
                          <time dateTime={activity.timestamp}>
                            {formatDateTime(activity.timestamp)}
                          </time>
                        </td>
                        <td>
                          <strong>{activity.action}</strong>
                        </td>
                        <td>{activity.context}</td>
                        <td>
                          <span className={`result-label result-label--${activity.tone}`}>
                            {activity.result}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="content-section" aria-labelledby="project-health-title">
            <div className="section-heading section-heading--split">
              <div>
                <h2 id="project-health-title">Project health</h2>
                <p>Latest source, snapshot, and document status by active project.</p>
              </div>
              <button
                type="button"
                className="button button--secondary"
                onClick={() => onNavigate("Projects")}
              >
                Open projects
              </button>
            </div>

            {dashboard.projectRows.length === 0 ? (
              <div className="empty-state empty-state--compact">
                <h3>No active projects</h3>
                <p>Create a project before importing technical sources.</p>
              </div>
            ) : (
              <div className="table-frame table-frame--dense">
                <table>
                  <caption className="visually-hidden">Active project operational health</caption>
                  <thead>
                    <tr>
                      <th scope="col">Project</th>
                      <th scope="col">Sources</th>
                      <th scope="col">Operations</th>
                      <th scope="col">Latest sync</th>
                      <th scope="col">Document</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboard.projectRows.map((row) => (
                      <tr key={row.project.id}>
                        <td>
                          <strong>{row.project.name}</strong>
                          <span className="table-secondary-text">{row.project.key}</span>
                        </td>
                        <td>{row.sourceCount}</td>
                        <td>{row.operationCount}</td>
                        <td>
                          <span className={`result-label result-label--${row.syncTone}`}>
                            {row.latestSync}
                          </span>
                        </td>
                        <td>{row.documentState}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </>
  );
}

function MetricCard({
  label,
  value,
  detail,
  tone = "neutral",
  onClick,
}: {
  label: string;
  value: number;
  detail: string;
  tone?: "neutral" | "warning";
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={`metric-card metric-card--${tone}`}
      onClick={onClick}
      aria-label={`${label}: ${value}. ${detail}`}
    >
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </button>
  );
}

function QuickAction({
  title,
  detail,
  onClick,
}: {
  title: string;
  detail: string;
  onClick: () => void;
}) {
  return (
    <button type="button" className="quick-action" onClick={onClick}>
      <span>
        <strong>{title}</strong>
        <small>{detail}</small>
      </span>
      <span aria-hidden="true">→</span>
    </button>
  );
}

function buildDashboard(data: OverviewData) {
  const readySources = data.sources.filter((source) => source.status === "READY");
  const completedRuns = data.runs.filter((run) => run.status === "COMPLETED");
  const failedRuns = data.runs.filter((run) => run.status === "FAILED");
  const pendingDocuments = data.documents.filter(
    (document) =>
      document.status === "IN_REVIEW" || document.status === "CHANGES_REQUESTED",
  );

  const latestRunsBySource = newestBy(
    data.runs,
    (run) => run.source_id,
    (run) => run.completed_at ?? run.started_at,
  );
  const latestDocumentsBySeries = newestBy(
    data.documents,
    (document) => document.document_id,
    (document) => document.updated_at,
  );

  const completedSourceIds = new Set(completedRuns.map((run) => run.source_id));
  const sourcesWithoutSnapshot = readySources.filter(
    (source) => !completedSourceIds.has(source.id),
  );
  const latestCompletedRunsBySource = newestBy(
    completedRuns,
    (run) => run.source_id,
    (run) => run.completed_at ?? run.started_at,
  );
  const breakingFindings = [...latestDocumentsBySeries.values()].reduce(
    (total, document) => total + document.breaking_change_count,
    0,
  );

  const attention = [
    failedRuns.length > 0
      ? {
          label: "Failed synchronizations",
          value: failedRuns.length,
          detail: "Inspect source integrity or parser errors.",
          tone: "danger" as const,
          target: "API Catalog" as const,
        }
      : null,
    sourcesWithoutSnapshot.length > 0
      ? {
          label: "Sources without a completed snapshot",
          value: sourcesWithoutSnapshot.length,
          detail: "Synchronize ready sources before generating documents.",
          tone: "warning" as const,
          target: "API Catalog" as const,
        }
      : null,
    pendingDocuments.length > 0
      ? {
          label: "Document versions awaiting action",
          value: pendingDocuments.length,
          detail: "Review approval status or requested changes.",
          tone: "warning" as const,
          target: "Documents" as const,
        }
      : null,
    breakingFindings > 0
      ? {
          label: "Breaking findings in current document versions",
          value: breakingFindings,
          detail: "Validate impact before approving an official release.",
          tone: "danger" as const,
          target: "Changes" as const,
        }
      : null,
  ].filter((item): item is NonNullable<typeof item> => item !== null);

  const projectById = new Map(data.projects.map((project) => [project.id, project]));
  const sourceById = new Map(data.sources.map((source) => [source.id, source]));

  const activities: ActivityItem[] = [
    ...data.runs.map((run) => ({
      id: `sync-${run.id}`,
      timestamp: run.completed_at ?? run.started_at,
      action: "Source synchronization",
      context: sourceById.get(run.source_id)?.name ?? "Unknown source",
      result: formatStatus(run.status),
      tone:
        run.status === "COMPLETED"
          ? ("success" as const)
          : run.status === "FAILED"
            ? ("danger" as const)
            : ("neutral" as const),
    })),
    ...data.documents.map((document) => ({
      id: `document-${document.id}`,
      timestamp: document.updated_at,
      action: `Document v${document.version}`,
      context:
        projectById.get(document.project_id)?.name ??
        document.title.replace("Technical Source Overview — ", ""),
      result: formatStatus(document.status),
      tone:
        document.status === "APPROVED"
          ? ("success" as const)
          : document.status === "CHANGES_REQUESTED"
            ? ("warning" as const)
            : ("neutral" as const),
    })),
  ]
    .sort((left, right) => timestampValue(right.timestamp) - timestampValue(left.timestamp))
    .slice(0, 6);

  const projectRows = data.projects.map((project) => {
    const projectSources = readySources.filter((source) => source.project_id === project.id);
    const latestRuns = projectSources
      .map((source) => latestRunsBySource.get(source.id))
      .filter((run): run is SynchronizationRun => run !== undefined);
    const latestRun = [...latestRuns].sort(
      (left, right) =>
        timestampValue(right.completed_at ?? right.started_at) -
        timestampValue(left.completed_at ?? left.started_at),
    )[0];
    const operationCount = projectSources
      .map((source) => latestCompletedRunsBySource.get(source.id))
      .filter((run): run is SynchronizationRun => run !== undefined)
      .reduce((total, run) => total + run.operation_count, 0);
    const projectDocuments = [...latestDocumentsBySeries.values()].filter(
      (document) => document.project_id === project.id,
    );
    const approvedDocument = projectDocuments
      .filter((document) => document.status === "APPROVED")
      .sort(
        (left, right) =>
          timestampValue(right.approved_at ?? right.updated_at) -
          timestampValue(left.approved_at ?? left.updated_at),
      )[0];
    const pendingCount = projectDocuments.filter(
      (document) =>
        document.status === "IN_REVIEW" || document.status === "CHANGES_REQUESTED",
    ).length;

    return {
      project,
      sourceCount: projectSources.length,
      operationCount,
      latestSync: latestRun ? formatStatus(latestRun.status) : "Not synchronized",
      syncTone:
        latestRun?.status === "COMPLETED"
          ? ("success" as const)
          : latestRun?.status === "FAILED"
            ? ("danger" as const)
            : ("neutral" as const),
      documentState: approvedDocument
        ? `Approved v${approvedDocument.version}`
        : pendingCount > 0
          ? `${pendingCount} pending review`
          : "No approved version",
    };
  });

  return {
    activeProjects: data.projects.length,
    readySources: readySources.length,
    completedSnapshots: completedRuns.length,
    pendingReviews: pendingDocuments.length,
    attention,
    activities,
    projectRows,
  };
}

function newestBy<T>(
  items: T[],
  key: (item: T) => string,
  timestamp: (item: T) => string,
): Map<string, T> {
  const result = new Map<string, T>();
  for (const item of items) {
    const current = result.get(key(item));
    if (
      current === undefined ||
      timestampValue(timestamp(item)) > timestampValue(timestamp(current))
    ) {
      result.set(key(item), item);
    }
  }
  return result;
}

function timestampValue(value: string): number {
  const timestamp = new Date(value).getTime();
  return Number.isNaN(timestamp) ? 0 : timestamp;
}

function formatDateTime(value: string): string {
  const timestamp = new Date(value);
  if (Number.isNaN(timestamp.getTime())) {
    return "Unknown";
  }
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(timestamp);
}

function formatStatus(value: string): string {
  return value
    .toLowerCase()
    .split("_")
    .map((part) => `${part.charAt(0).toUpperCase()}${part.slice(1)}`)
    .join(" ");
}
