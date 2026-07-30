import { useEffect, useMemo, useState } from "react";

import { Icon, type IconName } from "../../shared/ui/Icon";
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
            Current source, synchronization, and documentation state across the workspace.
          </p>
        </div>
        <div className="page-actions" aria-label="Quick actions">
          <button
            type="button"
            className="button button--secondary"
            onClick={() => onNavigate("Sources")}
          >
            <Icon name="upload" size={15} />
            Import source
          </button>
          <button
            type="button"
            className="button button--primary"
            onClick={() => onNavigate("Documents")}
          >
            <Icon name="documents" size={15} />
            Generate document
          </button>
        </div>
      </header>

      {serviceState === "unavailable" && (
        <div className="notice notice--error" role="alert">
          <span className="notice__icon" aria-hidden="true">
            <Icon name="alert" size={17} />
          </span>
          <span className="notice__body">
            <strong>Backend API is offline</strong>
            <small>Operational data may be unavailable until the service is started.</small>
          </span>
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
          <span className="notice__icon" aria-hidden="true">
            <Icon name="alert" size={17} />
          </span>
          <span className="notice__body">
            <strong>Operational overview could not load</strong>
            <small>{loadError}</small>
          </span>
          <button
            type="button"
            className="button button--secondary"
            onClick={() => globalThis.location.reload()}
          >
            <Icon name="refresh" size={15} />
            Reload
          </button>
        </div>
      )}

      {loadState === "ready" && (
        <div className="operational-dashboard">
          <section className="signal-region" aria-labelledby="workspace-metrics-title">
            <div className="signal-region__heading">
              <div>
                <h2 id="workspace-metrics-title">Workspace metrics</h2>
                <p>Live operational signals from existing platform APIs.</p>
              </div>
              <span className="data-provenance">
                <span className="data-provenance__dot" aria-hidden="true" />
                Live data {serviceVersion ? `· API v${serviceVersion}` : ""}
              </span>
            </div>

            <div className="signal-strip">
              <SignalItem
                icon="projects"
                label="Active projects"
                value={dashboard.activeProjects}
                detail="Workspace boundaries"
                onClick={() => onNavigate("Projects")}
              />
              <SignalItem
                icon="source"
                label="Ready sources"
                value={dashboard.readySources}
                detail="Validated artifacts"
                onClick={() => onNavigate("Sources")}
              />
              <SignalItem
                icon="sync"
                label="Completed snapshots"
                value={dashboard.completedSnapshots}
                detail="Successful sync runs"
                onClick={() => onNavigate("API Catalog")}
              />
              <SignalItem
                icon="review"
                label="Pending reviews"
                value={dashboard.pendingReviews}
                detail="Lifecycle actions"
                tone={dashboard.pendingReviews > 0 ? "warning" : "neutral"}
                onClick={() => onNavigate("Documents")}
              />
            </div>
          </section>

          <div className="operations-workbench">
            <div className="operations-main">
              <section className="operations-section" aria-labelledby="recent-activity-title">
                <div className="operations-section__heading">
                  <div>
                    <p className="section-kicker">Event stream</p>
                    <h2 id="recent-activity-title">Recent activity</h2>
                    <p>Latest synchronization and document lifecycle events.</p>
                  </div>
                  <span className="record-count">{dashboard.activities.length} activities</span>
                </div>

                {dashboard.activities.length === 0 ? (
                  <div className="empty-state empty-state--compact">
                    <span className="empty-state__icon" aria-hidden="true">
                      <Icon name="activity" size={19} />
                    </span>
                    <div>
                      <h3>No activity yet</h3>
                      <p>Import and synchronize a source to begin the traceable workflow.</p>
                    </div>
                  </div>
                ) : (
                  <ol className="activity-stream" aria-label="Recent synchronization and document activities">
                    {dashboard.activities.map((activity) => (
                      <li key={activity.id}>
                        <span
                          className={`activity-stream__icon activity-stream__icon--${activity.tone}`}
                          aria-hidden="true"
                        >
                          <Icon
                            name={activity.action.startsWith("Document") ? "documents" : "sync"}
                            size={16}
                          />
                        </span>
                        <span className="activity-stream__content">
                          <strong>{activity.action}</strong>
                          <small>{activity.context}</small>
                        </span>
                        <span className="activity-stream__meta">
                          <span className={`result-label result-label--${activity.tone}`}>
                            {activity.result}
                          </span>
                          <time dateTime={activity.timestamp}>
                            {formatDateTime(activity.timestamp)}
                          </time>
                        </span>
                      </li>
                    ))}
                  </ol>
                )}
              </section>

              <section className="operations-section" aria-labelledby="project-health-title">
                <div className="operations-section__heading">
                  <div>
                    <p className="section-kicker">Coverage matrix</p>
                    <h2 id="project-health-title">Project health</h2>
                    <p>Latest source, snapshot, and document state by active project.</p>
                  </div>
                  <button
                    type="button"
                    className="text-action"
                    onClick={() => onNavigate("Projects")}
                  >
                    Open projects
                    <Icon name="arrow-right" size={14} />
                  </button>
                </div>

                {dashboard.projectRows.length === 0 ? (
                  <div className="empty-state empty-state--compact">
                    <span className="empty-state__icon" aria-hidden="true">
                      <Icon name="projects" size={19} />
                    </span>
                    <div>
                      <h3>No active projects</h3>
                      <p>Create a project before importing technical sources.</p>
                    </div>
                  </div>
                ) : (
                  <div className="table-frame table-frame--dense health-table">
                    <table>
                      <caption className="visually-hidden">
                        Active project operational health
                      </caption>
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
                            <td className="numeric-cell">{row.sourceCount}</td>
                            <td className="numeric-cell">{row.operationCount}</td>
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
            </div>

            <aside className="operations-rail" aria-label="Operational actions">
              <section className="rail-section" aria-labelledby="attention-title">
                <div className="rail-section__heading">
                  <span className="rail-section__icon rail-section__icon--warning" aria-hidden="true">
                    <Icon name="alert" size={16} />
                  </span>
                  <div>
                    <h2 id="attention-title">Attention required</h2>
                    <p>Conditions that may block publication.</p>
                  </div>
                  {dashboard.attention.length > 0 && (
                    <span className="rail-count">
                      {formatCount(dashboard.attention.length, "condition")}
                    </span>
                  )}
                </div>

                {dashboard.attention.length === 0 ? (
                  <div className="attention-clear">
                    <span className="attention-clear__icon" aria-hidden="true">
                      <Icon name="check" size={17} />
                    </span>
                    <span>
                      <strong>No operational issues detected</strong>
                      <small>Available source-backed checks are clear.</small>
                    </span>
                  </div>
                ) : (
                  <ul className="attention-list">
                    {dashboard.attention.map((item) => (
                      <li key={item.label}>
                        <span
                          className={`attention-severity attention-severity--${item.tone}`}
                          aria-label={`${item.value} ${item.label.toLowerCase()}`}
                        >
                          {item.value}
                        </span>
                        <span className="attention-list__copy">
                          <strong>{item.label}</strong>
                          <small>{item.detail}</small>
                        </span>
                        <button
                          type="button"
                          className="icon-action"
                          aria-label={`Review ${item.label}`}
                          onClick={() => onNavigate(item.target)}
                        >
                          <Icon name="arrow-right" size={15} />
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </section>

              <section className="rail-section" aria-labelledby="quick-actions-title">
                <div className="rail-section__heading">
                  <span className="rail-section__icon" aria-hidden="true">
                    <Icon name="activity" size={16} />
                  </span>
                  <div>
                    <h2 id="quick-actions-title">Quick actions</h2>
                    <p>Continue the source-to-document workflow.</p>
                  </div>
                </div>

                <div className="quick-action-list">
                  <QuickAction
                    icon="projects"
                    title="Manage projects"
                    detail="Create or archive boundaries."
                    onClick={() => onNavigate("Projects")}
                  />
                  <QuickAction
                    icon="upload"
                    title="Import OpenAPI"
                    detail="Register a JSON or YAML artifact."
                    onClick={() => onNavigate("Sources")}
                  />
                  <QuickAction
                    icon="sync"
                    title="Synchronize catalog"
                    detail="Create a normalized snapshot."
                    onClick={() => onNavigate("API Catalog")}
                  />
                  <QuickAction
                    icon="review"
                    title="Review documents"
                    detail="Open approval and revision history."
                    onClick={() => onNavigate("Documents")}
                  />
                </div>
              </section>

              <div className="rail-footnote">
                <Icon name="server" size={14} />
                <span>
                  Data is assembled from deterministic project, source, synchronization,
                  and document APIs.
                </span>
              </div>
            </aside>
          </div>
        </div>
      )}
    </>
  );
}

function SignalItem({
  icon,
  label,
  value,
  detail,
  tone = "neutral",
  onClick,
}: {
  icon: IconName;
  label: string;
  value: number;
  detail: string;
  tone?: "neutral" | "warning";
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={`signal-item signal-item--${tone}`}
      onClick={onClick}
      aria-label={`${label}: ${value}. ${detail}`}
    >
      <span className="signal-item__icon" aria-hidden="true">
        <Icon name={icon} size={17} />
      </span>
      <span className="signal-item__copy">
        <span>{label}</span>
        <small>{detail}</small>
      </span>
      <strong>{value}</strong>
    </button>
  );
}

function QuickAction({
  icon,
  title,
  detail,
  onClick,
}: {
  icon: IconName;
  title: string;
  detail: string;
  onClick: () => void;
}) {
  return (
    <button type="button" className="quick-action" onClick={onClick}>
      <span className="quick-action__icon" aria-hidden="true">
        <Icon name={icon} size={16} />
      </span>
      <span className="quick-action__copy">
        <strong>{title}</strong>
        <small>{detail}</small>
      </span>
      <Icon className="quick-action__arrow" name="arrow-right" size={14} />
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

function formatCount(value: number, singular: string): string {
  return `${value} ${value === 1 ? singular : `${singular}s`}`;
}

function formatStatus(value: string): string {
  if (value === "SUPERSEDED") {
    return "Replaced";
  }
  return value
    .toLowerCase()
    .split("_")
    .map((part) => `${part.charAt(0).toUpperCase()}${part.slice(1)}`)
    .join(" ");
}
