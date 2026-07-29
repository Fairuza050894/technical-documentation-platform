import { useEffect, useMemo, useState } from "react";

import { listSynchronizations } from "../catalog/api";
import type { SynchronizationRun } from "../catalog/types";
import { listProjects } from "../projects/api";
import type { ProjectCollection } from "../projects/types";
import { listSources } from "../sources/api";
import type { TechnicalSource } from "../sources/types";
import {
  generateTechnicalSourceOverview,
  getDocumentDownloadUrl,
  getGeneratedDocument,
  listGeneratedDocuments,
} from "./api";
import type {
  GeneratedDocumentDetail,
  GeneratedDocumentSummary,
} from "./types";

interface SnapshotOption {
  run: SynchronizationRun;
  source: TechnicalSource;
}

export function DocumentsWorkspace() {
  const [projects, setProjects] = useState<ProjectCollection>({ items: [], total: 0 });
  const [projectId, setProjectId] = useState("");
  const [snapshots, setSnapshots] = useState<SnapshotOption[]>([]);
  const [targetRunId, setTargetRunId] = useState("");
  const [baselineRunId, setBaselineRunId] = useState("");
  const [documents, setDocuments] = useState<GeneratedDocumentSummary[]>([]);
  const [selectedDocument, setSelectedDocument] =
    useState<GeneratedDocumentDetail | null>(null);
  const [message, setMessage] = useState("Select a completed synchronization snapshot.");
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    void listProjects().then((collection) => {
      setProjects(collection);
      setProjectId(collection.items.find((item) => item.status === "ACTIVE")?.id ?? "");
    });
  }, []);

  useEffect(() => {
    if (!projectId) {
      setSnapshots([]);
      setDocuments([]);
      setTargetRunId("");
      setBaselineRunId("");
      setSelectedDocument(null);
      return;
    }

    void Promise.all([loadSnapshots(projectId), listGeneratedDocuments(projectId)]).then(
      ([snapshotOptions, documentCollection]) => {
        setSnapshots(snapshotOptions);
        setDocuments(documentCollection.items);
        setTargetRunId(snapshotOptions[0]?.run.id ?? "");
        setBaselineRunId(snapshotOptions[1]?.run.id ?? "");
        setSelectedDocument(null);
        setMessage(
          snapshotOptions.length === 0
            ? "Synchronize an OpenAPI source before generating a document."
            : "Select a target snapshot and an optional baseline.",
        );
      },
    );
  }, [projectId]);

  const availableBaselines = useMemo(
    () => snapshots.filter(({ run }) => run.id !== targetRunId),
    [snapshots, targetRunId],
  );

  async function generate(): Promise<void> {
    if (!projectId || !targetRunId || isGenerating) {
      return;
    }

    setIsGenerating(true);
    setMessage("Generating deterministic Markdown…");
    try {
      const document = await generateTechnicalSourceOverview(
        projectId,
        targetRunId,
        baselineRunId || null,
      );
      setSelectedDocument(document);
      setDocuments((current) => [
        document,
        ...current.filter((item) => item.id !== document.id),
      ]);
      setMessage("Technical Source Overview generated.");
    } catch (error: unknown) {
      setMessage(error instanceof Error ? error.message : "Document generation failed.");
    } finally {
      setIsGenerating(false);
    }
  }

  async function openDocument(documentId: string): Promise<void> {
    setMessage("Loading generated document…");
    try {
      const document = await getGeneratedDocument(documentId);
      setSelectedDocument(document);
      setMessage("Generated document loaded.");
    } catch (error: unknown) {
      setMessage(error instanceof Error ? error.message : "Document could not be loaded.");
    }
  }

  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">Deterministic document generation</p>
          <h1>Documents</h1>
        </div>
        <span className="environment-badge">Markdown output</span>
      </header>

      <section className="content-section" aria-labelledby="document-generator-title">
        <div className="section-heading">
          <div>
            <h2 id="document-generator-title">Generate Technical Source Overview</h2>
            <p>
              Render source-backed Markdown from a normalized snapshot. A baseline adds a
              deterministic breaking-change summary.
            </p>
          </div>
        </div>

        {projects.total === 0 ? (
          <div className="empty-state">
            <h3>Create a project first</h3>
            <p>Generated documents require a project and a completed synchronization.</p>
          </div>
        ) : (
          <div className="form-panel">
            <div className="form-grid">
              <div className="field">
                <label htmlFor="document-project">Project</label>
                <select
                  id="document-project"
                  value={projectId}
                  onChange={(event) => setProjectId(event.target.value)}
                >
                  {projects.items.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.key} — {project.name}
                    </option>
                  ))}
                </select>
              </div>

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
            </div>

            <div className="form-actions">
              <button
                className="button button--primary"
                type="button"
                disabled={!targetRunId || isGenerating}
                onClick={() => void generate()}
              >
                {isGenerating ? "Generating…" : "Generate overview"}
              </button>
            </div>
          </div>
        )}
        <p className="loading-state" role="status">
          {message}
        </p>
      </section>

      <section className="content-section" aria-labelledby="document-history-title">
        <div className="section-heading section-heading--split">
          <div>
            <h2 id="document-history-title">Generation history</h2>
            <p>Each generation is stored with its input snapshot and content checksum.</p>
          </div>
          <span className="record-count">{documents.length} documents</span>
        </div>

        {documents.length === 0 ? (
          <div className="empty-state">
            <h3>No generated documents</h3>
            <p>Generate the first Technical Source Overview from a completed snapshot.</p>
          </div>
        ) : (
          <div className="table-frame">
            <table>
              <thead>
                <tr>
                  <th>Document</th>
                  <th>Snapshot</th>
                  <th>Content</th>
                  <th>Generated</th>
                  <th className="table-action-column">Action</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((document) => (
                  <tr key={document.id}>
                    <td>
                      <strong>{document.title}</strong>
                      <span className="table-secondary-text">{document.file_name}</span>
                    </td>
                    <td>
                      <code>{document.target_run_id.slice(0, 8)}</code>
                      <span className="table-secondary-text">
                        Baseline: {document.baseline_run_id?.slice(0, 8) ?? "None"}
                      </span>
                    </td>
                    <td>
                      {document.operation_count} operations · {document.schema_count} schemas
                      <span className="table-secondary-text">
                        {document.breaking_change_count} breaking changes
                      </span>
                    </td>
                    <td>{new Date(document.generated_at).toLocaleString()}</td>
                    <td className="table-action-column">
                      <button
                        className="button button--secondary"
                        type="button"
                        onClick={() => void openDocument(document.id)}
                      >
                        Preview
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selectedDocument !== null && (
        <section className="content-section" aria-labelledby="document-preview-title">
          <div className="section-heading section-heading--split">
            <div>
              <h2 id="document-preview-title">{selectedDocument.title}</h2>
              <p>
                SHA-256 <code>{selectedDocument.checksum}</code>
              </p>
            </div>
            <a
              className="button button--secondary"
              href={getDocumentDownloadUrl(selectedDocument.id)}
              download={selectedDocument.file_name}
            >
              Download Markdown
            </a>
          </div>
          <pre className="document-preview">{selectedDocument.content}</pre>
        </section>
      )}
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
            {source.name} · {new Date(run.started_at).toLocaleString()}
          </option>
        ))}
      </select>
    </div>
  );
}
