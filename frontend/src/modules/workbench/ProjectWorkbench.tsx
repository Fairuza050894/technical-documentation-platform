import { useEffect, useMemo, useState } from "react";

import type { ProjectStage } from "../../app/router";
import { Icon, type IconName } from "../../shared/ui/Icon";
import { ApiCatalogWorkspace } from "../catalog/ApiCatalogWorkspace";
import { listSynchronizations } from "../catalog/api";
import type { SynchronizationRun } from "../catalog/types";
import { ChangesWorkspace } from "../changes/ChangesWorkspace";
import { DocumentsWorkspace } from "../documents/DocumentsWorkspace";
import { listGeneratedDocuments } from "../documents/api";
import type { GeneratedDocumentSummary } from "../documents/types";
import { listProjects } from "../projects/api";
import type { Project } from "../projects/types";
import { SourceWorkspace } from "../sources/SourceWorkspace";
import { listSources } from "../sources/api";
import type { TechnicalSource } from "../sources/types";

interface ProjectWorkbenchProps {
  projectId: string;
  stage: ProjectStage;
  onNavigateStage: (stage: ProjectStage) => void;
  onBackToProjects: () => void;
  onProjectResolved: (project: Project | null) => void;
}

interface ProjectSummary {
  sources: TechnicalSource[];
  runs: SynchronizationRun[];
  documents: GeneratedDocumentSummary[];
}

type LoadState = "loading" | "ready" | "not-found" | "error";

const stageItems: ReadonlyArray<{
  id: ProjectStage;
  label: string;
  icon: IconName;
  description: string;
}> = [
  { id: "overview", label: "Overview", icon: "overview", description: "Project readiness" },
  { id: "sources", label: "Sources", icon: "source", description: "Technical intake" },
  { id: "catalog", label: "API Catalog", icon: "catalog", description: "Normalized snapshot" },
  { id: "changes", label: "Changes", icon: "changes", description: "Deterministic comparison" },
  { id: "documents", label: "Documents", icon: "documents", description: "Version lifecycle" },
];

export function ProjectWorkbench({
  projectId,
  stage,
  onNavigateStage,
  onBackToProjects,
  onProjectResolved,
}: ProjectWorkbenchProps) {
  const [project, setProject] = useState<Project | null>(null);
  const [summary, setSummary] = useState<ProjectSummary>({
    sources: [],
    runs: [],
    documents: [],
  });
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [loadError, setLoadError] = useState("");
  const [summaryError, setSummaryError] = useState("");

  useEffect(() => {
    let active = true;
    onProjectResolved(null);
    setProject(null);
    setSummary({ sources: [], runs: [], documents: [] });
    setLoadState("loading");
    setLoadError("");
    setSummaryError("");

    async function loadProject(): Promise<void> {
      try {
        const collection = await listProjects();
        const resolved = collection.items.find((item) => item.id === projectId) ?? null;
        if (!active) {
          return;
        }
        if (resolved === null) {
          setLoadState("not-found");
          return;
        }

        setProject(resolved);
        onProjectResolved(resolved);
        setLoadState("ready");

        try {
          const sourceCollection = await listSources(resolved.id);
          const readySources = sourceCollection.items.filter(
            (source) => source.status === "READY",
          );
          const [runCollections, documentCollection] = await Promise.all([
            Promise.all(readySources.map((source) => listSynchronizations(source.id))),
            listGeneratedDocuments(resolved.id),
          ]);
          if (!active) {
            return;
          }
          setSummary({
            sources: sourceCollection.items,
            runs: runCollections.flatMap((collectionItem) => collectionItem.items),
            documents: documentCollection.items,
          });
        } catch (error: unknown) {
          if (active) {
            setSummaryError(
              error instanceof Error
                ? error.message
                : "Project readiness could not be calculated.",
            );
          }
        }
      } catch (error: unknown) {
        if (!active) {
          return;
        }
        setLoadError(
          error instanceof Error ? error.message : "The project workspace could not load.",
        );
        setLoadState("error");
      }
    }

    void loadProject();
    return () => {
      active = false;
    };
  }, [onProjectResolved, projectId]);

  const nextAction = useMemo(
    () => (project === null ? null : resolveNextAction(project, summary)),
    [project, summary],
  );

  if (loadState === "loading") {
    return (
      <div className="project-workbench-state" role="status">
        <span className="loading-bar" aria-hidden="true" />
        Loading project workspace…
      </div>
    );
  }

  if (loadState === "not-found") {
    return (
      <section className="content-section project-workbench-state" aria-labelledby="project-not-found-title">
        <span className="project-workbench-state__icon" aria-hidden="true">
          <Icon name="alert" size={22} />
        </span>
        <h1 id="project-not-found-title">Project not found</h1>
        <p>The project in this URL no longer exists or is not available.</p>
        <button type="button" className="button button--primary" onClick={onBackToProjects}>
          Open project registry
        </button>
      </section>
    );
  }

  if (loadState === "error" || project === null) {
    return (
      <section className="content-section project-workbench-state" aria-labelledby="project-error-title">
        <span className="project-workbench-state__icon" aria-hidden="true">
          <Icon name="alert" size={22} />
        </span>
        <h1 id="project-error-title">Project workspace unavailable</h1>
        <p>{loadError || "The selected project could not be loaded."}</p>
        <button type="button" className="button button--secondary" onClick={onBackToProjects}>
          Back to projects
        </button>
      </section>
    );
  }

  return (
    <div className="project-workbench">
      <header className="project-workbench-header">
        <div className="project-workbench-header__identity">
          <p className="eyebrow">Project workbench</p>
          <div className="project-workbench-title">
            <span className="project-workbench-title__icon" aria-hidden="true">
              <Icon name="folder" size={20} />
            </span>
            <div>
              <h1>{project.name}</h1>
              <p>{project.description || "No project description provided."}</p>
            </div>
          </div>
        </div>
        <div className="project-workbench-header__meta">
          <span className="project-key-badge">{project.key}</span>
          <span
            className={
              project.status === "ACTIVE"
                ? "status-indicator status-indicator--success"
                : "status-indicator status-indicator--neutral"
            }
          >
            {project.status === "ACTIVE" ? "Active" : "Archived"}
          </span>
        </div>
      </header>

      {project.status === "ARCHIVED" && (
        <div className="notice notice--warning" role="status">
          <span className="notice__icon" aria-hidden="true">
            <Icon name="alert" size={17} />
          </span>
          <span className="notice__body">
            <strong>This project is archived</strong>
            <small>Existing evidence remains available, but new intake may be restricted.</small>
          </span>
        </div>
      )}

      <nav className="project-stage-navigation" aria-label="Project workflow">
        <ol>
          {stageItems.map((item, index) => (
            <li key={item.id}>
              <button
                type="button"
                className={
                  item.id === stage ? "project-stage-button is-active" : "project-stage-button"
                }
                aria-current={item.id === stage ? "step" : undefined}
                onClick={() => onNavigateStage(item.id)}
              >
                <span className="project-stage-button__index">{index + 1}</span>
                <span className="project-stage-button__icon" aria-hidden="true">
                  <Icon name={item.icon} size={16} />
                </span>
                <span className="project-stage-button__copy">
                  <strong>{item.label}</strong>
                  <small>{item.description}</small>
                </span>
              </button>
            </li>
          ))}
          <li className="project-stage-planned" aria-label="Review stage planned">
            <span>6</span>
            <strong>Review</strong>
            <small>Planned</small>
          </li>
          <li className="project-stage-planned" aria-label="Release stage planned">
            <span>7</span>
            <strong>Release</strong>
            <small>Planned</small>
          </li>
        </ol>
      </nav>

      {stage === "overview" && nextAction !== null && (
        <ProjectOverview
          project={project}
          summary={summary}
          summaryError={summaryError}
          nextAction={nextAction}
          onNavigateStage={onNavigateStage}
        />
      )}

      <div className="embedded-workspace">
        {stage === "sources" && <SourceWorkspace project={project} embedded />}
        {stage === "catalog" && <ApiCatalogWorkspace project={project} embedded />}
        {stage === "changes" && <ChangesWorkspace project={project} embedded />}
        {stage === "documents" && <DocumentsWorkspace project={project} embedded />}
      </div>
    </div>
  );
}

function ProjectOverview({
  project,
  summary,
  summaryError,
  nextAction,
  onNavigateStage,
}: {
  project: Project;
  summary: ProjectSummary;
  summaryError: string;
  nextAction: NextAction;
  onNavigateStage: (stage: ProjectStage) => void;
}) {
  const readySources = summary.sources.filter((source) => source.status === "READY");
  const completedRuns = summary.runs.filter((run) => run.status === "COMPLETED");
  const openReviews = summary.documents.filter((document) =>
    ["IN_REVIEW", "CHANGES_REQUESTED"].includes(document.status),
  );

  return (
    <div className="project-overview">
      <section className="next-action-panel" aria-labelledby="next-action-title">
        <div className="next-action-panel__icon" aria-hidden="true">
          <Icon name={nextAction.icon} size={20} />
        </div>
        <div className="next-action-panel__copy">
          <p className="section-kicker">Next recommended action</p>
          <h2 id="next-action-title">{nextAction.title}</h2>
          <p>{nextAction.detail}</p>
        </div>
        <button
          type="button"
          className="button button--primary"
          onClick={() => onNavigateStage(nextAction.stage)}
          disabled={project.status === "ARCHIVED" && nextAction.stage !== "overview"}
        >
          {nextAction.actionLabel}
          <Icon name="arrow-right" size={15} />
        </button>
      </section>

      {summaryError && (
        <div className="notice notice--error" role="alert">
          <span>{summaryError}</span>
        </div>
      )}

      <section className="project-summary-grid" aria-label="Project readiness summary">
        <SummaryCard
          icon="source"
          label="Ready sources"
          value={readySources.length}
          detail={`${summary.sources.length} total source records`}
          onClick={() => onNavigateStage("sources")}
        />
        <SummaryCard
          icon="sync"
          label="Completed snapshots"
          value={completedRuns.length}
          detail={`${summary.runs.length} synchronization runs`}
          onClick={() => onNavigateStage("catalog")}
        />
        <SummaryCard
          icon="documents"
          label="Document versions"
          value={summary.documents.length}
          detail={`${openReviews.length} require workflow attention`}
          onClick={() => onNavigateStage("documents")}
        />
        <SummaryCard
          icon="changes"
          label="Change readiness"
          value={completedRuns.length >= 2 ? 1 : 0}
          detail={
            completedRuns.length >= 2
              ? "Snapshot comparison is available"
              : "Two completed snapshots are required"
          }
          onClick={() => onNavigateStage("changes")}
        />
      </section>

      <section className="content-section project-workflow-map" aria-labelledby="project-workflow-title">
        <div className="section-heading">
          <div>
            <h2 id="project-workflow-title">Documentation workflow</h2>
            <p>Current project context persists while you move between technical stages.</p>
          </div>
        </div>
        <ol>
          <WorkflowStep label="Source intake" state={readySources.length > 0 ? "complete" : "current"} />
          <WorkflowStep label="Synchronization" state={completedRuns.length > 0 ? "complete" : readySources.length > 0 ? "current" : "pending"} />
          <WorkflowStep label="Change analysis" state={completedRuns.length >= 2 ? "available" : "pending"} />
          <WorkflowStep label="Document lifecycle" state={summary.documents.length > 0 ? "complete" : completedRuns.length > 0 ? "current" : "pending"} />
          <WorkflowStep label="Review and release" state="planned" />
        </ol>
      </section>
    </div>
  );
}

interface NextAction {
  stage: ProjectStage;
  icon: IconName;
  title: string;
  detail: string;
  actionLabel: string;
}

function resolveNextAction(project: Project, summary: ProjectSummary): NextAction {
  if (project.status === "ARCHIVED") {
    return {
      stage: "overview",
      icon: "alert",
      title: "Review archived project evidence",
      detail: "This project is read-only. Existing sources and documents remain available.",
      actionLabel: "Review overview",
    };
  }

  const readySources = summary.sources.filter((source) => source.status === "READY");
  if (readySources.length === 0) {
    return {
      stage: "sources",
      icon: "upload",
      title: "Import the first technical source",
      detail: "Add a validated OpenAPI JSON or YAML file to establish project evidence.",
      actionLabel: "Open source intake",
    };
  }

  const completedRuns = summary.runs.filter((run) => run.status === "COMPLETED");
  if (completedRuns.length === 0) {
    return {
      stage: "catalog",
      icon: "sync",
      title: "Create the first normalized snapshot",
      detail: "Synchronize a ready source before generating or comparing documentation.",
      actionLabel: "Open API catalog",
    };
  }

  if (summary.documents.length === 0) {
    return {
      stage: "documents",
      icon: "documents",
      title: "Generate the first document version",
      detail: "A completed snapshot is available and no document version exists yet.",
      actionLabel: "Generate document",
    };
  }

  const workflowAttention = summary.documents.some((document) =>
    ["IN_REVIEW", "CHANGES_REQUESTED"].includes(document.status),
  );
  if (workflowAttention) {
    return {
      stage: "documents",
      icon: "review",
      title: "Continue document review",
      detail: "At least one version is waiting for approval or requested changes.",
      actionLabel: "Open document workflow",
    };
  }

  if (completedRuns.length >= 2) {
    return {
      stage: "changes",
      icon: "changes",
      title: "Review source changes",
      detail: "Multiple completed snapshots are available for deterministic comparison.",
      actionLabel: "Compare snapshots",
    };
  }

  return {
    stage: "documents",
    icon: "documents",
    title: "Continue governed documentation",
    detail: "Review the latest version and prepare the next lifecycle action.",
    actionLabel: "Open documents",
  };
}

function SummaryCard({
  icon,
  label,
  value,
  detail,
  onClick,
}: {
  icon: IconName;
  label: string;
  value: number;
  detail: string;
  onClick: () => void;
}) {
  return (
    <button type="button" className="project-summary-card" onClick={onClick}>
      <span className="project-summary-card__icon" aria-hidden="true">
        <Icon name={icon} size={17} />
      </span>
      <span className="project-summary-card__copy">
        <small>{label}</small>
        <strong>{value}</strong>
        <span>{detail}</span>
      </span>
      <Icon className="project-summary-card__arrow" name="arrow-right" size={15} />
    </button>
  );
}

function WorkflowStep({
  label,
  state,
}: {
  label: string;
  state: "complete" | "current" | "available" | "pending" | "planned";
}) {
  return (
    <li className={`workflow-step workflow-step--${state}`}>
      <span className="workflow-step__marker" aria-hidden="true">
        {state === "complete" ? <Icon name="check" size={14} /> : null}
      </span>
      <strong>{label}</strong>
      <small>{formatWorkflowState(state)}</small>
    </li>
  );
}

function formatWorkflowState(
  state: "complete" | "current" | "available" | "pending" | "planned",
): string {
  switch (state) {
    case "complete":
      return "Complete";
    case "current":
      return "Next";
    case "available":
      return "Available";
    case "pending":
      return "Pending evidence";
    case "planned":
      return "Planned";
  }
}
