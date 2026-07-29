import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { listProjects } from "../projects/api";
import type { Project } from "../projects/types";
import { ApiClientError } from "../../shared/api/client";
import { archiveSource, importOpenApiSource, listSources } from "./api";
import type { TechnicalSource } from "./types";

type LoadState = "loading" | "ready" | "error";

export function SourceWorkspace() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [sources, setSources] = useState<TechnicalSource[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [loadError, setLoadError] = useState("");
  const [sourceName, setSourceName] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [formError, setFormError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pendingArchiveId, setPendingArchiveId] = useState<string | null>(null);

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedProjectId) ?? null,
    [projects, selectedProjectId],
  );

  const loadProjects = useCallback(async (signal?: AbortSignal): Promise<void> => {
    setLoadState("loading");
    setLoadError("");
    try {
      const response = await listProjects(signal);
      setProjects(response.items);
      const firstProject = response.items.find((project) => project.status === "ACTIVE");
      setSelectedProjectId((current) => current || firstProject?.id || response.items[0]?.id || "");
      if (response.items.length === 0) {
        setSources([]);
        setLoadState("ready");
      }
    } catch (error: unknown) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      setLoadError("Projects could not be loaded. Confirm that the backend is running.");
      setLoadState("error");
    }
  }, []);

  const loadSources = useCallback(async (projectId: string, signal?: AbortSignal): Promise<void> => {
    setLoadState("loading");
    setLoadError("");
    try {
      const response = await listSources(projectId, signal);
      setSources(response.items);
      setLoadState("ready");
    } catch (error: unknown) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      setLoadError("Sources could not be loaded for the selected project.");
      setLoadState("error");
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void loadProjects(controller.signal);
    return () => controller.abort();
  }, [loadProjects]);

  useEffect(() => {
    if (!selectedProjectId) {
      return;
    }
    const controller = new AbortController();
    void loadSources(selectedProjectId, controller.signal);
    return () => controller.abort();
  }, [loadSources, selectedProjectId]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setFormError("");
    if (!selectedProjectId || !selectedFile) {
      setFormError("Select an active project and an OpenAPI JSON or YAML file.");
      return;
    }

    setIsSubmitting(true);
    try {
      const imported = await importOpenApiSource(selectedProjectId, sourceName, selectedFile);
      setSources((current) => [imported, ...current]);
      setSourceName("");
      setSelectedFile(null);
      const fileInput = document.getElementById("openapi-file") as HTMLInputElement | null;
      if (fileInput) {
        fileInput.value = "";
      }
    } catch (error: unknown) {
      setFormError(
        error instanceof ApiClientError ? error.message : "The OpenAPI source could not be imported.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleArchive(source: TechnicalSource): Promise<void> {
    try {
      const archived = await archiveSource(source.id);
      setSources((current) =>
        current.map((item) => (item.id === archived.id ? archived : item)),
      );
      setPendingArchiveId(null);
    } catch (error: unknown) {
      setLoadError(
        error instanceof ApiClientError ? error.message : "The source could not be archived.",
      );
    }
  }

  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">Source intake</p>
          <h1>Sources</h1>
        </div>
        <span className="environment-badge">Local artifacts</span>
      </header>

      <section className="content-section" aria-labelledby="source-registry-title">
        <div className="section-heading section-heading--split">
          <div>
            <h2 id="source-registry-title">OpenAPI source registry</h2>
            <p>Validated JSON and YAML specifications remain traceable to their original file.</p>
          </div>
          <span className="record-count">
            {sources.length} {sources.length === 1 ? "source" : "sources"}
          </span>
        </div>

        <div className="workspace-filter">
          <label htmlFor="source-project">Project</label>
          <select
            id="source-project"
            value={selectedProjectId}
            onChange={(event) => setSelectedProjectId(event.target.value)}
            disabled={projects.length === 0}
          >
            {projects.length === 0 && <option value="">No projects available</option>}
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.key} — {project.name} {project.status === "ARCHIVED" ? "(Archived)" : ""}
              </option>
            ))}
          </select>
        </div>

        {loadState === "error" && (
          <div className="notice notice--error" role="alert">
            <span>{loadError}</span>
            <button
              type="button"
              className="button button--secondary"
              onClick={() =>
                selectedProjectId ? void loadSources(selectedProjectId) : void loadProjects()
              }
            >
              Retry
            </button>
          </div>
        )}

        {loadState === "loading" && <p className="loading-state">Loading sources…</p>}

        {loadState === "ready" && projects.length === 0 && (
          <div className="empty-state">
            <h3>Create a project first</h3>
            <p>Sources require a project boundary before they can be imported.</p>
          </div>
        )}

        {loadState === "ready" && projects.length > 0 && sources.length === 0 && (
          <div className="empty-state">
            <h3>No sources for this project</h3>
            <p>Import an OpenAPI specification to create the first source-backed record.</p>
          </div>
        )}

        {sources.length > 0 && (
          <div className="table-frame">
            <table>
              <thead>
                <tr>
                  <th scope="col">Source</th>
                  <th scope="col">Specification</th>
                  <th scope="col">Coverage</th>
                  <th scope="col">Status</th>
                  <th scope="col" className="table-action-column">Action</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((source) => (
                  <tr key={source.id}>
                    <td>
                      <strong>{source.name}</strong>
                      <span className="table-secondary-text">
                        {source.original_file_name} · {source.media_type}
                      </span>
                      <code className="checksum-text" title={`SHA-256 ${source.checksum}`}>
                        sha256:{source.checksum.slice(0, 12)}…
                      </code>
                    </td>
                    <td>
                      <span>{source.api_title}</span>
                      <span className="table-secondary-text">
                        OpenAPI {source.openapi_version} · API {source.api_version}
                      </span>
                    </td>
                    <td>
                      <span>{source.operation_count} operations</span>
                      <span className="table-secondary-text">{source.path_count} paths</span>
                    </td>
                    <td>
                      <span
                        className={
                          source.status === "READY"
                            ? "status-indicator status-indicator--success"
                            : "status-indicator status-indicator--neutral"
                        }
                      >
                        {source.status === "READY" ? "Ready" : "Archived"}
                      </span>
                    </td>
                    <td className="table-action-column">
                      {pendingArchiveId === source.id ? (
                        <span className="inline-actions">
                          <button
                            type="button"
                            className="button button--danger-quiet"
                            onClick={() => void handleArchive(source)}
                          >
                            Confirm archive
                          </button>
                          <button
                            type="button"
                            className="button button--quiet"
                            onClick={() => setPendingArchiveId(null)}
                          >
                            Cancel
                          </button>
                        </span>
                      ) : (
                        <button
                          type="button"
                          className="button button--quiet"
                          disabled={source.status === "ARCHIVED"}
                          onClick={() => setPendingArchiveId(source.id)}
                        >
                          {source.status === "ARCHIVED" ? "Archived" : "Archive"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="content-section" aria-labelledby="import-source-title">
        <div className="section-heading">
          <div>
            <h2 id="import-source-title">Import OpenAPI file</h2>
            <p>The deterministic validator supports OpenAPI 3.0.x and 3.1.x.</p>
          </div>
        </div>

        <form className="form-panel" onSubmit={(event) => void handleSubmit(event)}>
          <div className="form-grid">
            <div className="field">
              <label htmlFor="source-name">Source name</label>
              <input
                id="source-name"
                required
                minLength={3}
                maxLength={80}
                value={sourceName}
                onChange={(event) => setSourceName(event.target.value)}
                placeholder="Commerce OpenAPI"
              />
              <small>Stable display name within the selected project.</small>
            </div>

            <div className="field">
              <label htmlFor="openapi-file">OpenAPI file</label>
              <input
                id="openapi-file"
                type="file"
                required
                accept=".json,.yaml,.yml,application/json,application/yaml,text/yaml"
                onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
              />
              <small>UTF-8 JSON/YAML, maximum 5 MiB. The file is never executed.</small>
            </div>
          </div>

          {selectedProject?.status === "ARCHIVED" && (
            <p className="form-error" role="alert">
              Select an active project before importing a source.
            </p>
          )}
          {formError && <p className="form-error" role="alert">{formError}</p>}

          <div className="form-actions">
            <button
              type="submit"
              className="button button--primary"
              disabled={
                isSubmitting ||
                projects.length === 0 ||
                selectedProject?.status === "ARCHIVED"
              }
            >
              {isSubmitting ? "Importing…" : "Import source"}
            </button>
          </div>
        </form>
      </section>
    </>
  );
}
