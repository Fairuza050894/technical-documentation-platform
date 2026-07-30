import { useEffect, useMemo, useState } from "react";

import { requestJson } from "../../shared/api/client";
import type { ProjectCollection } from "../projects/types";
import { listSources } from "../sources/api";
import type { TechnicalSource } from "../sources/types";
import { listSynchronizations } from "../catalog/api";
import type { SynchronizationRun } from "../catalog/types";
import { compareSnapshots } from "./api";
import type { ComparisonResult } from "./types";

interface SnapshotOption {
  run: SynchronizationRun;
  source: TechnicalSource;
}

interface ChangesWorkspaceProps {
  project?: ProjectCollection["items"][number];
  embedded?: boolean;
}

export function ChangesWorkspace({
  project,
  embedded = false,
}: ChangesWorkspaceProps = {}) {
  const [projects, setProjects] = useState<ProjectCollection>(
    project ? { items: [project], total: 1 } : { items: [], total: 0 },
  );
  const [projectId, setProjectId] = useState(project?.id ?? "");
  const [snapshots, setSnapshots] = useState<SnapshotOption[]>([]);
  const [baselineId, setBaselineId] = useState("");
  const [targetId, setTargetId] = useState("");
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [message, setMessage] = useState("Select two completed snapshots.");

  useEffect(() => {
    if (project) {
      setProjects({ items: [project], total: 1 });
      setProjectId(project.id);
      return;
    }
    void requestJson<ProjectCollection>("/projects").then((collection) => {
      setProjects(collection);
      setProjectId(collection.items.find((item) => item.status === "ACTIVE")?.id ?? "");
    });
  }, [project]);

  useEffect(() => {
    if (!projectId) {
      setSnapshots([]);
      return;
    }
    void listSources(projectId).then(async (collection) => {
      const activeSources = collection.items.filter((source) => source.status === "READY");
      const runs = await Promise.all(
        activeSources.map(async (source) => ({
          source,
          runs: (await listSynchronizations(source.id)).items,
        })),
      );
      const options = runs.flatMap(({ source, runs: sourceRuns }) =>
        sourceRuns
          .filter((run) => run.status === "COMPLETED")
          .map((run) => ({ run, source })),
      );
      setSnapshots(options);
      setBaselineId(options.at(-1)?.run.id ?? "");
      setTargetId(options[0]?.run.id ?? "");
      setResult(null);
    });
  }, [projectId]);

  const canCompare = baselineId !== "" && targetId !== "" && baselineId !== targetId;
  const summary = useMemo(() => {
    if (result === null) return null;
    return {
      added: result.changes.filter((item) => item.kind === "ADDED").length,
      modified: result.changes.filter((item) => item.kind === "MODIFIED").length,
      removed: result.changes.filter((item) => item.kind === "REMOVED").length,
    };
  }, [result]);

  async function compare(): Promise<void> {
    if (!canCompare) return;
    setMessage("Comparing snapshots…");
    try {
      const comparison = await compareSnapshots(projectId, baselineId, targetId);
      setResult(comparison);
      setMessage(comparison.total === 0 ? "No deterministic changes detected." : "Comparison completed.");
    } catch (error: unknown) {
      setMessage(error instanceof Error ? error.message : "Comparison failed.");
    }
  }

  return (
    <>
      {!embedded && (
        <header className="topbar">
          <div>
            <p className="eyebrow">Deterministic comparison</p>
            <h1>Changes</h1>
          </div>
          <span className="environment-badge">Snapshot evidence</span>
        </header>
      )}

      <section className="content-section" aria-labelledby="comparison-title">
        <div className="section-heading">
          <div>
            <h2 id="comparison-title">Compare synchronization snapshots</h2>
            <p>Compare normalized operations and schemas without AI-generated facts.</p>
          </div>
        </div>

        <div className="form-panel">
          <div className="form-grid">
            {!project && (
              <div className="field">
                <label htmlFor="change-project">Project</label>
                <select
                  id="change-project"
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
            <SnapshotSelect id="baseline-snapshot" label="Baseline" value={baselineId} options={snapshots} onChange={setBaselineId} />
            <SnapshotSelect id="target-snapshot" label="Target" value={targetId} options={snapshots} onChange={setTargetId} />
          </div>
          <div className="form-actions">
            <button className="button button--primary" type="button" disabled={!canCompare} onClick={() => void compare()}>
              Compare snapshots
            </button>
          </div>
        </div>
        <p className="loading-state" role="status">{message}</p>
      </section>

      {result !== null && summary !== null && (
        <section className="content-section" aria-labelledby="change-results-title">
          <div className="section-heading section-heading--split">
            <div>
              <h2 id="change-results-title">Comparison result</h2>
              <p>{result.breaking_total} breaking changes require review.</p>
            </div>
            <span className="record-count">{result.total} changes</span>
          </div>
          <div className="status-grid">
            <article className="status-card"><span className="status-label">Added</span><strong>{summary.added}</strong></article>
            <article className="status-card"><span className="status-label">Modified</span><strong>{summary.modified}</strong></article>
            <article className="status-card"><span className="status-label">Removed</span><strong>{summary.removed}</strong></article>
          </div>
          <div className="catalog-list">
            {result.changes.map((change) => (
              <article className="catalog-card" key={`${change.entity_type}-${change.entity_key}-${change.kind}`}>
                <div className="catalog-card__heading">
                  <div><span className="method-badge">{change.entity_type}</span><strong>{change.entity_key}</strong></div>
                  <span className="status-indicator status-indicator--neutral">{change.severity}</span>
                </div>
                <p>{change.summary}</p>
                <dl className="detail-list">
                  <div><dt>Change</dt><dd>{change.kind}</dd></div>
                  <div><dt>Before evidence</dt><dd><code>{change.before_pointer || "Not applicable"}</code></dd></div>
                  <div><dt>After evidence</dt><dd><code>{change.after_pointer || "Not applicable"}</code></dd></div>
                </dl>
              </article>
            ))}
          </div>
        </section>
      )}
    </>
  );
}

function SnapshotSelect({ id, label, value, options, onChange }: {
  id: string;
  label: string;
  value: string;
  options: SnapshotOption[];
  onChange: (value: string) => void;
}) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select id={id} value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Select snapshot</option>
        {options.map(({ run, source }) => (
          <option key={run.id} value={run.id}>
            {source.name} · {new Date(run.started_at).toLocaleString()}
          </option>
        ))}
      </select>
    </div>
  );
}
