import { useEffect, useMemo, useState } from "react";

import { listSynchronizations } from "../catalog/api";
import type { SynchronizationRun } from "../catalog/types";
import { listProjects } from "../projects/api";
import type { ProjectCollection } from "../projects/types";
import { listSources } from "../sources/api";
import { getCurrentIdentity } from "../../shared/identity/api";
import type { CurrentIdentity } from "../../shared/identity/types";
import type { TechnicalSource } from "../sources/types";
import {
  approveDocumentVersion,
  compareDocumentVersions,
  generateTechnicalSourceOverview,
  getDocumentDownloadUrl,
  getGeneratedDocument,
  listGeneratedDocuments,
  listWorkflowEvents,
  requestDocumentChanges,
  submitDocumentForReview,
  supersedeDocumentVersion,
} from "./api";
import type {
  DocumentSectionChangeKind,
  DocumentVersionComparison,
  GeneratedDocumentDetail,
  GeneratedDocumentSummary,
  WorkflowEvent,
} from "./types";

interface SnapshotOption {
  run: SynchronizationRun;
  source: TechnicalSource;
}

type WorkflowAction = "submit-review" | "request-changes" | "approve" | "supersede";
type ChangeFilter = "ALL" | DocumentSectionChangeKind;

interface DocumentsWorkspaceProps {
  project?: ProjectCollection["items"][number];
  embedded?: boolean;
}

export function DocumentsWorkspace({
  project,
  embedded = false,
}: DocumentsWorkspaceProps = {}) {
  const [projects, setProjects] = useState<ProjectCollection>(
    project ? { items: [project], total: 1 } : { items: [], total: 0 },
  );
  const [projectId, setProjectId] = useState(project?.id ?? "");
  const [snapshots, setSnapshots] = useState<SnapshotOption[]>([]);
  const [targetRunId, setTargetRunId] = useState("");
  const [baselineRunId, setBaselineRunId] = useState("");
  const [versions, setVersions] = useState<GeneratedDocumentSummary[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<GeneratedDocumentDetail | null>(null);
  const [workflowEvents, setWorkflowEvents] = useState<WorkflowEvent[]>([]);
  const [identity, setIdentity] = useState<CurrentIdentity | null>(null);
  const [identityError, setIdentityError] = useState("");
  const [revisionReason, setRevisionReason] = useState("");
  const [workflowComment, setWorkflowComment] = useState("");
  const [comparisonBaselineId, setComparisonBaselineId] = useState("");
  const [comparisonTargetId, setComparisonTargetId] = useState("");
  const [comparison, setComparison] = useState<DocumentVersionComparison | null>(null);
  const [changeFilter, setChangeFilter] = useState<ChangeFilter>("ALL");
  const [message, setMessage] = useState("Select a completed synchronization snapshot.");
  const [isBusy, setIsBusy] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    void getCurrentIdentity(controller.signal)
      .then((resolvedIdentity) => {
        setIdentity(resolvedIdentity);
        setIdentityError("");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setIdentity(null);
        setIdentityError(
          error instanceof Error ? error.message : "Current identity could not be resolved.",
        );
      });

    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (project) {
      setProjects({ items: [project], total: 1 });
      setProjectId(project.id);
      return;
    }
    void listProjects().then((collection) => {
      setProjects(collection);
      setProjectId(collection.items.find((item) => item.status === "ACTIVE")?.id ?? "");
    });
  }, [project]);

  useEffect(() => {
    let isCurrent = true;

    if (!projectId) {
      setSnapshots([]);
      setVersions([]);
      setTargetRunId("");
      setBaselineRunId("");
      setSelectedVersion(null);
      setWorkflowEvents([]);
      setComparison(null);
      setComparisonBaselineId("");
      setComparisonTargetId("");
      setChangeFilter("ALL");
      return () => {
        isCurrent = false;
      };
    }

    async function load(): Promise<void> {
      setMessage("Loading document workspace…");
      try {
        const [snapshotOptions, documentCollection] = await Promise.all([
          loadSnapshots(projectId),
          listGeneratedDocuments(projectId),
        ]);
        if (!isCurrent) {
          return;
        }
        setSnapshots(snapshotOptions);
        setVersions(documentCollection.items);
        setTargetRunId(snapshotOptions[0]?.run.id ?? "");
        setBaselineRunId(snapshotOptions[1]?.run.id ?? "");
        setSelectedVersion(null);
        setWorkflowEvents([]);
        setComparison(null);
        setChangeFilter("ALL");
        setComparisonTargetId(documentCollection.items[0]?.id ?? "");
        setComparisonBaselineId(documentCollection.items[1]?.id ?? "");
        setMessage(
          snapshotOptions.length === 0
            ? "Synchronize an OpenAPI source before generating a document."
            : "Select a target snapshot and an optional baseline.",
        );
      } catch (error: unknown) {
        if (isCurrent) {
          setMessage(
            error instanceof Error ? error.message : "Document workspace could not load.",
          );
        }
      }
    }

    void load();
    return () => {
      isCurrent = false;
    };
  }, [projectId]);

  const availableBaselines = useMemo(
    () => snapshots.filter(({ run }) => run.id !== targetRunId),
    [snapshots, targetRunId],
  );

  const selectedSeriesVersions = useMemo(() => {
    if (selectedVersion === null) {
      return versions;
    }
    return versions.filter((version) => version.document_id === selectedVersion.document_id);
  }, [selectedVersion, versions]);

  const currentVersionId = selectedSeriesVersions[0]?.id ?? null;
  const approvedVersionId =
    selectedSeriesVersions.find((version) => version.status === "APPROVED")?.id ?? null;
  const selectedReplacement =
    selectedVersion === null ? null : findReplacementVersion(selectedVersion, versions);

  const comparisonVersions = useMemo(() => {
    const documentId =
      selectedVersion?.document_id ?? versions[0]?.document_id ?? null;
    return documentId === null
      ? []
      : versions.filter((version) => version.document_id === documentId);
  }, [selectedVersion, versions]);

  const filteredChanges = useMemo(() => {
    if (comparison === null || changeFilter === "ALL") {
      return comparison?.changes ?? [];
    }
    return comparison.changes.filter((change) => change.kind === changeFilter);
  }, [changeFilter, comparison]);

  function configureComparison(items: GeneratedDocumentSummary[]): void {
    setComparison(null);
    setChangeFilter("ALL");
    setComparisonTargetId(items[0]?.id ?? "");
    setComparisonBaselineId(items[1]?.id ?? "");
  }

  async function refreshVersions(preferredVersionId?: string): Promise<void> {
    if (!projectId) {
      return;
    }
    const collection = await listGeneratedDocuments(projectId);
    setVersions(collection.items);
    configureComparison(collection.items);
    const versionId = preferredVersionId ?? selectedVersion?.id;
    if (versionId && collection.items.some((item) => item.id === versionId)) {
      await openVersion(versionId, false);
    }
  }

  async function generate(): Promise<void> {
    if (!projectId || !targetRunId || isBusy) {
      return;
    }

    setIsBusy(true);
    setMessage("Generating deterministic Markdown…");
    try {
      const document = await generateTechnicalSourceOverview(
        projectId,
        targetRunId,
        baselineRunId || null,
        revisionReason,
      );
      await refreshVersions(document.id);
      setRevisionReason("");
      setMessage(
        document.reused_existing_version
          ? `Version ${document.version} already contains this content. Existing version reused.`
          : `Version ${document.version} generated as ${document.status}.`,
      );
    } catch (error: unknown) {
      setMessage(error instanceof Error ? error.message : "Document generation failed.");
    } finally {
      setIsBusy(false);
    }
  }

  async function openVersion(versionId: string, announce = true): Promise<void> {
    if (announce) {
      setMessage("Loading document version…");
    }
    try {
      const [document, events] = await Promise.all([
        getGeneratedDocument(versionId),
        listWorkflowEvents(versionId),
      ]);
      setSelectedVersion(document);
      setWorkflowEvents(events.items);
      setWorkflowComment("");
      const seriesVersions = versions.filter(
        (version) => version.document_id === document.document_id,
      );
      setComparisonTargetId(document.id);
      setComparisonBaselineId(
        seriesVersions.find((version) => version.id !== document.id)?.id ?? "",
      );
      setComparison(null);
      if (announce) {
        setMessage(`Version ${document.version} loaded.`);
      }
    } catch (error: unknown) {
      setMessage(error instanceof Error ? error.message : "Document version could not load.");
    }
  }

  async function runWorkflow(action: WorkflowAction): Promise<void> {
    if (selectedVersion === null || isBusy) {
      return;
    }

    setIsBusy(true);
    setMessage("Applying document workflow action…");
    try {
      const handlers: Record<WorkflowAction, () => Promise<GeneratedDocumentDetail>> = {
        "submit-review": () =>
          submitDocumentForReview(selectedVersion.id, workflowComment),
        "request-changes": () =>
          requestDocumentChanges(selectedVersion.id, workflowComment),
        approve: () =>
          approveDocumentVersion(selectedVersion.id, workflowComment),
        supersede: () =>
          supersedeDocumentVersion(selectedVersion.id, workflowComment),
      };
      const updated = await handlers[action]();
      await refreshVersions(updated.id);
      setWorkflowComment("");
      setMessage(`Version ${updated.version} is now ${formatStatus(updated.status)}.`);
    } catch (error: unknown) {
      setMessage(error instanceof Error ? error.message : "Workflow action failed.");
    } finally {
      setIsBusy(false);
    }
  }

  async function compareVersions(): Promise<void> {
    if (!comparisonBaselineId || !comparisonTargetId || isBusy) {
      return;
    }

    setIsBusy(true);
    setMessage("Comparing structured document sections…");
    try {
      const result = await compareDocumentVersions(
        comparisonBaselineId,
        comparisonTargetId,
      );
      setComparison(result);
      setChangeFilter("ALL");
      setMessage(`Comparison completed with ${result.total} section changes.`);
    } catch (error: unknown) {
      setMessage(error instanceof Error ? error.message : "Version comparison failed.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <>
      {!embedded && (
        <header className="topbar">
          <div>
            <p className="eyebrow">Governed document lifecycle</p>
            <h1>Documents</h1>
          </div>
          <span className="environment-badge">Versioned Markdown</span>
        </header>
      )}

      <section
        className="content-section document-section"
        aria-labelledby="document-generator-title"
      >
        <div className="section-heading">
          <div>
            <h2 id="document-generator-title">Generate Technical Source Overview</h2>
            <p>
              Create an immutable draft version from a normalized snapshot. Identical content
              reuses the existing checksum-backed version.
            </p>
          </div>
        </div>

        {projects.total === 0 ? (
          <div className="empty-state">
            <h3>Create a project first</h3>
            <p>Generated documents require a project and a completed synchronization.</p>
          </div>
        ) : (
          <div className="form-panel document-generation-form">
            <div className="form-grid">
              {!project && (
                <div className="field">
                  <label htmlFor="document-project">Project</label>
                  <select
                    id="document-project"
                    value={projectId}
                    onChange={(event) => setProjectId(event.target.value)}
                  >
                    {projects.items.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.key} — {item.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <SnapshotSelect
                id="document-target"
                label="Target snapshot"
                value={targetRunId}
                options={snapshots}
                onChange={(value) => {
                  setTargetRunId(value);
                  if (baselineRunId === value) {
                    setBaselineRunId("");
                  }
                }}
              />

              <SnapshotSelect
                id="document-baseline"
                label="Baseline snapshot (optional)"
                value={baselineRunId}
                options={availableBaselines}
                allowEmpty
                onChange={setBaselineRunId}
              />

              <IdentitySummary
                label="Generated by"
                identity={identity}
                errorMessage={identityError}
              />

              <div className="field field--wide">
                <label htmlFor="revision-reason">Revision reason</label>
                <textarea
                  className="document-revision-reason"
                  id="revision-reason"
                  value={revisionReason}
                  maxLength={500}
                  placeholder="Describe why this version is being generated."
                  onChange={(event) => setRevisionReason(event.target.value)}
                />
              </div>
            </div>

            <div className="form-actions">
              <button
                className="button button--primary"
                type="button"
                disabled={!targetRunId || identity === null || isBusy || project?.status === "ARCHIVED"}
                onClick={() => void generate()}
              >
                {isBusy ? "Working…" : "Generate version"}
              </button>
            </div>
          </div>
        )}
        <p className="loading-state document-generation-status" role="status">
          {message}
        </p>
      </section>

      <section
        className="content-section document-section document-section--history"
        aria-labelledby="document-history-title"
      >
        <div className="section-heading section-heading--split">
          <div>
            <h2 id="document-history-title">Version history</h2>
            <p>Every distinct checksum is stored as an immutable document version.</p>
          </div>
          <span className="record-count">{formatCount(versions.length, "version")}</span>
        </div>

        {versions.length === 0 ? (
          <div className="empty-state">
            <h3>No document versions</h3>
            <p>Generate the first Technical Source Overview from a completed snapshot.</p>
          </div>
        ) : (
          <div className="table-frame">
            <table>
              <thead>
                <tr>
                  <th>Version</th>
                  <th>Status</th>
                  <th>Source snapshot</th>
                  <th>Revision</th>
                  <th>Generated</th>
                  <th className="table-action-column">Action</th>
                </tr>
              </thead>
              <tbody>
                {versions.map((version) => {
                  const replacement = findReplacementVersion(version, versions);
                  const isLatestVersion =
                    version.id === currentVersionId && version.status !== "SUPERSEDED";
                  return (
                  <tr key={version.id} className={selectedVersion?.id === version.id ? "is-selected" : undefined}>
                    <td>
                      <strong>v{version.version}</strong>
                      <span className="table-secondary-text">{version.title}</span>
                    </td>
                    <td>
                      <StatusBadge
                        status={version.status}
                        label={
                          version.status === "SUPERSEDED" && replacement === null
                            ? "Previous version"
                            : undefined
                        }
                      />
                      {isLatestVersion && (
                        <span className="table-secondary-text">Latest version</span>
                      )}
                      {version.status === "SUPERSEDED" && (
                        <span className="table-secondary-text">
                          {replacement ? `Replaced by v${replacement.version}` : "No longer current"}
                        </span>
                      )}
                      {version.id === approvedVersionId && (
                        <span className="table-secondary-text">Current approved</span>
                      )}
                    </td>
                    <td>
                      <code>{version.target_run_id.slice(0, 8)}</code>
                      <span className="table-secondary-text">
                        Baseline: {version.baseline_run_id?.slice(0, 8) ?? "None"}
                      </span>
                    </td>
                    <td>
                      {version.revision_reason || "No revision reason"}
                      <span className="table-secondary-text">By {version.created_by}</span>
                    </td>
                    <td>{formatDate(version.generated_at)}</td>
                    <td className="table-action-column">
                      <button
                        className="button button--secondary"
                        type="button"
                        onClick={() => void openVersion(version.id)}
                      >
                        Open
                      </button>
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selectedVersion !== null && (
        <section
          className="content-section document-section document-section--detail"
          aria-labelledby="document-detail-title"
        >
          <div className="section-heading section-heading--split">
            <div>
              <p className="eyebrow">Version {selectedVersion.version}</p>
              <h2 id="document-detail-title">{selectedVersion.title}</h2>
              <div className="document-detail-badges">
                <StatusBadge
                  status={selectedVersion.status}
                  label={
                    selectedVersion.status === "SUPERSEDED" && selectedReplacement === null
                      ? "Previous version"
                      : undefined
                  }
                />
                {selectedVersion.id === currentVersionId &&
                  selectedVersion.status !== "SUPERSEDED" && (
                    <span className="status-badge">Latest version</span>
                  )}
                {selectedVersion.id === approvedVersionId && <span className="status-badge status-badge--approved">Official approved</span>}
              </div>
            </div>
            <a
              className="button button--secondary"
              href={getDocumentDownloadUrl(selectedVersion.id)}
              download={selectedVersion.file_name}
            >
              Download Markdown
            </a>
          </div>

          <dl className="document-metadata-grid">
            <Metadata label="Document ID" value={selectedVersion.document_id} code />
            <Metadata label="Version ID" value={selectedVersion.id} code />
            <Metadata label="Checksum" value={selectedVersion.checksum} code />
            <Metadata label="Created by" value={selectedVersion.created_by} />
            <Metadata label="Revision reason" value={selectedVersion.revision_reason || "Not provided"} />
            <Metadata
              label="Catalog content"
              value={`${selectedVersion.operation_count} operations · ${selectedVersion.schema_count} schemas · ${selectedVersion.breaking_change_count} breaking changes`}
            />
          </dl>

          <div className="document-workspace-grid">
            <article className="document-panel" aria-labelledby="workflow-actions-title">
              <h3 id="workflow-actions-title">Review and approval</h3>
              <p>Available actions follow the immutable document lifecycle.</p>
              <IdentitySummary
                label="Acting identity"
                identity={identity}
                errorMessage={identityError}
              />
              <div className="field">
                <label htmlFor="workflow-comment">Review comment</label>
                <textarea
                  id="workflow-comment"
                  value={workflowComment}
                  maxLength={1000}
                  placeholder="Record the review decision or requested change."
                  onChange={(event) => setWorkflowComment(event.target.value)}
                />
              </div>
              <WorkflowActions
                version={selectedVersion}
                comment={workflowComment}
                disabled={isBusy}
                onAction={(action) => void runWorkflow(action)}
              />
            </article>

            <article className="document-panel" aria-labelledby="workflow-history-title">
              <div className="section-heading section-heading--split">
                <div>
                  <h3 id="workflow-history-title">Workflow timeline</h3>
                  <p>{workflowEvents.length} recorded events</p>
                </div>
              </div>
              {workflowEvents.length === 0 ? (
                <p className="loading-state">No workflow events were found.</p>
              ) : (
                <ol className="workflow-timeline">
                  {workflowEvents.map((event) => (
                    <li key={event.id}>
                      <div>
                        <strong>{formatAction(event.action)}</strong>
                        <span>{formatDate(event.created_at)}</span>
                      </div>
                      <p>
                        {event.actor} · {formatStatus(event.new_status)}
                      </p>
                      {event.comment && <blockquote>{event.comment}</blockquote>}
                    </li>
                  ))}
                </ol>
              )}
            </article>
          </div>

          <details className="document-preview-disclosure" open>
            <summary>Markdown preview</summary>
            <pre className="document-preview">{selectedVersion.content}</pre>
          </details>
        </section>
      )}

      <section
        className="content-section document-section document-section--comparison"
        aria-labelledby="version-comparison-title"
      >
        <div className="section-heading">
          <div>
            <h2 id="version-comparison-title">Compare document versions</h2>
            <p>
              Compare deterministic level-two Markdown sections without using AI or line-order
              heuristics.
            </p>
          </div>
        </div>

        {comparisonVersions.length < 2 ? (
          <div className="empty-state">
            <h3>Two versions required</h3>
            <p>Generate another distinct document version before running a comparison.</p>
          </div>
        ) : (
          <div className="comparison-toolbar">
            <VersionSelect
              id="comparison-baseline"
              label="Baseline version"
              value={comparisonBaselineId}
              versions={comparisonVersions.filter(
                (version) => version.id !== comparisonTargetId,
              )}
              onChange={setComparisonBaselineId}
            />
            <VersionSelect
              id="comparison-target"
              label="Target version"
              value={comparisonTargetId}
              versions={comparisonVersions.filter(
                (version) => version.id !== comparisonBaselineId,
              )}
              onChange={setComparisonTargetId}
            />
            <div className="catalog-toolbar__action">
              <button
                className="button button--primary"
                type="button"
                disabled={!comparisonBaselineId || !comparisonTargetId || isBusy}
                onClick={() => void compareVersions()}
              >
                Compare versions
              </button>
            </div>
          </div>
        )}

        {comparison !== null && (
          <div className="comparison-results">
            <div className="comparison-summary" aria-label="Version comparison summary">
              <SummaryMetric label="Total changes" value={comparison.total} />
              <SummaryMetric label="Added" value={comparison.added_total} />
              <SummaryMetric label="Modified" value={comparison.modified_total} />
              <SummaryMetric label="Removed" value={comparison.removed_total} />
            </div>

            <div className="workspace-filter">
              <label htmlFor="change-filter">Change filter</label>
              <select
                id="change-filter"
                value={changeFilter}
                onChange={(event) => setChangeFilter(event.target.value as ChangeFilter)}
              >
                <option value="ALL">All changes</option>
                <option value="ADDED">Added</option>
                <option value="MODIFIED">Modified</option>
                <option value="REMOVED">Removed</option>
              </select>
            </div>

            {filteredChanges.length === 0 ? (
              <div className="empty-state">
                <h3>No matching section changes</h3>
                <p>The selected versions are identical for this filter.</p>
              </div>
            ) : (
              <div className="table-frame">
                <table>
                  <thead>
                    <tr>
                      <th>Section</th>
                      <th>Change</th>
                      <th>Baseline evidence</th>
                      <th>Target evidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredChanges.map((change) => (
                      <tr key={`${change.section_key}-${change.kind}`}>
                        <td>
                          <strong>{change.section_title}</strong>
                          <span className="table-secondary-text">{change.section_key}</span>
                        </td>
                        <td>
                          <span className={`change-kind change-kind--${change.kind.toLowerCase()}`}>
                            {change.kind}
                          </span>
                        </td>
                        <td>
                          <span className="comparison-excerpt">
                            {change.before_excerpt || "Not present"}
                          </span>
                          {change.before_checksum && (
                            <code className="checksum-text">
                              {change.before_checksum.slice(0, 12)}
                            </code>
                          )}
                        </td>
                        <td>
                          <span className="comparison-excerpt">
                            {change.after_excerpt || "Not present"}
                          </span>
                          {change.after_checksum && (
                            <code className="checksum-text">
                              {change.after_checksum.slice(0, 12)}
                            </code>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </section>
    </>
  );
}

async function loadSnapshots(projectId: string): Promise<SnapshotOption[]> {
  const sourceCollection = await listSources(projectId);
  const activeSources = sourceCollection.items.filter((source) => source.status === "READY");
  const sourceRuns = await Promise.all(
    activeSources.map(async (source) => ({
      source,
      runs: (await listSynchronizations(source.id)).items,
    })),
  );

  return sourceRuns
    .flatMap(({ source, runs }) =>
      runs
        .filter((run) => run.status === "COMPLETED")
        .map((run) => ({ run, source })),
    )
    .sort(
      (left, right) =>
        new Date(right.run.started_at).getTime() -
        new Date(left.run.started_at).getTime(),
    );
}

function SnapshotSelect({
  id,
  label,
  value,
  options,
  allowEmpty = false,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  options: SnapshotOption[];
  allowEmpty?: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select id={id} value={value} onChange={(event) => onChange(event.target.value)}>
        {(allowEmpty || options.length === 0) && (
          <option value="">{allowEmpty ? "No baseline" : "Select snapshot"}</option>
        )}
        {options.map(({ run, source }) => (
          <option key={run.id} value={run.id}>
            {source.name} · {formatDate(run.started_at)}
          </option>
        ))}
      </select>
    </div>
  );
}

function VersionSelect({
  id,
  label,
  value,
  versions,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  versions: GeneratedDocumentSummary[];
  onChange: (value: string) => void;
}) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select id={id} value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Select version</option>
        {versions.map((version) => (
          <option key={version.id} value={version.id}>
            v{version.version} · {formatStatus(version.status)}
          </option>
        ))}
      </select>
    </div>
  );
}

function IdentitySummary({
  label,
  identity,
  errorMessage,
}: {
  label: string;
  identity: CurrentIdentity | null;
  errorMessage: string;
}) {
  return (
    <div className="field identity-summary" aria-live="polite">
      <span className="identity-summary__label">{label}</span>
      {identity === null ? (
        <span className={errorMessage ? "identity-summary__error" : "identity-summary__loading"}>
          {errorMessage || "Resolving server identity…"}
        </span>
      ) : (
        <>
          <strong>{identity.display_name}</strong>
          <small>
            {identity.provider} · {identity.assurance === "VERIFIED" ? "Verified" : "Development"}
          </small>
        </>
      )}
    </div>
  );
}


function WorkflowActions({
  version,
  comment,
  disabled,
  onAction,
}: {
  version: GeneratedDocumentDetail;
  comment: string;
  disabled: boolean;
  onAction: (action: WorkflowAction) => void;
}) {
  if (version.status === "DRAFT") {
    return (
      <button
        className="button button--primary"
        type="button"
        disabled={disabled}
        onClick={() => onAction("submit-review")}
      >
        Submit for review
      </button>
    );
  }
  if (version.status === "IN_REVIEW") {
    return (
      <div className="workflow-action-row">
        <button
          className="button button--primary"
          type="button"
          disabled={disabled}
          onClick={() => onAction("approve")}
        >
          Approve version
        </button>
        <button
          className="button button--secondary"
          type="button"
          disabled={disabled || comment.trim().length === 0}
          onClick={() => onAction("request-changes")}
        >
          Request changes
        </button>
      </div>
    );
  }
  if (version.status === "APPROVED") {
    return (
      <button
        className="button button--secondary"
        type="button"
        disabled={disabled}
        onClick={() => onAction("supersede")}
      >
        Mark as replaced
      </button>
    );
  }
  return (
    <p className="loading-state">
      {version.status === "CHANGES_REQUESTED"
        ? "Generate a revised version to address the requested changes."
        : "Replaced versions are read-only."}
    </p>
  );
}

function StatusBadge({
  status,
  label,
}: {
  status: GeneratedDocumentSummary["status"];
  label?: string;
}) {
  return (
    <span className={`status-badge status-badge--${status.toLowerCase()}`}>
      {label ?? formatStatus(status)}
    </span>
  );
}

function Metadata({
  label,
  value,
  code = false,
}: {
  label: string;
  value: string;
  code?: boolean;
}) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{code ? <code>{value}</code> : value}</dd>
    </div>
  );
}

function SummaryMetric({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function findReplacementVersion(
  version: GeneratedDocumentSummary,
  versions: GeneratedDocumentSummary[],
): GeneratedDocumentSummary | null {
  const newerVersions = versions
    .filter(
      (candidate) =>
        candidate.document_id === version.document_id &&
        versionNumber(candidate.version) > versionNumber(version.version),
    )
    .sort((left, right) => versionNumber(left.version) - versionNumber(right.version));
  return newerVersions[0] ?? null;
}

function versionNumber(value: string): number {
  const [major = "0", minor = "0"] = value.split(".");
  return Number(major) * 1000 + Number(minor);
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
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatAction(value: string): string {
  return formatStatus(value);
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}
