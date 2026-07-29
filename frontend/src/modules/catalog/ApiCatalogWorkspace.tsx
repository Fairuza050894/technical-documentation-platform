import { useCallback, useEffect, useMemo, useState } from "react";

import { listProjects } from "../projects/api";
import type { Project } from "../projects/types";
import { listSources } from "../sources/api";
import type { TechnicalSource } from "../sources/types";
import { getApiCatalog, synchronizeSource } from "./api";
import type { ApiCatalog, ApiOperation } from "./types";

type LoadState = "loading" | "ready" | "error";

const emptyCatalog: ApiCatalog = {
  runs: [],
  operations: [],
  schemas: [],
  operation_total: 0,
  schema_total: 0,
};

export function ApiCatalogWorkspace() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [sources, setSources] = useState<TechnicalSource[]>([]);
  const [catalog, setCatalog] = useState<ApiCatalog>(emptyCatalog);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [selectedSourceId, setSelectedSourceId] = useState("");
  const [selectedOperationKey, setSelectedOperationKey] = useState("");
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [loadError, setLoadError] = useState("");
  const [syncState, setSyncState] = useState<"idle" | "running">("idle");
  const [syncError, setSyncError] = useState("");

  const selectedSource = sources.find((source) => source.id === selectedSourceId);
  const selectedOperation = useMemo(
    () =>
      catalog.operations.find(
        (operation) => operationKey(operation) === selectedOperationKey,
      ) ?? catalog.operations[0],
    [catalog.operations, selectedOperationKey],
  );

  const loadProjectData = useCallback(
    async (
      projectId: string,
      sourceId: string,
      signal?: AbortSignal,
    ): Promise<void> => {
      const [sourceResponse, catalogResponse] = await Promise.all([
        listSources(projectId, signal),
        getApiCatalog(projectId, sourceId || undefined, signal),
      ]);
      setSources(sourceResponse.items);
      setCatalog(catalogResponse);
      setSelectedOperationKey(
        catalogResponse.operations[0] ? operationKey(catalogResponse.operations[0]) : "",
      );
      setLoadState("ready");
    },
    [],
  );

  useEffect(() => {
    const controller = new AbortController();

    async function loadInitialState(): Promise<void> {
      setLoadState("loading");
      try {
        const projectResponse = await listProjects(controller.signal);
        setProjects(projectResponse.items);
        const firstProjectId = projectResponse.items[0]?.id ?? "";
        setSelectedProjectId(firstProjectId);
        if (!firstProjectId) {
          setSources([]);
          setCatalog(emptyCatalog);
          setLoadState("ready");
          return;
        }
        await loadProjectData(firstProjectId, "", controller.signal);
      } catch (error: unknown) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setLoadError(error instanceof Error ? error.message : "The API catalog could not be loaded.");
        setLoadState("error");
      }
    }

    void loadInitialState();
    return () => controller.abort();
  }, [loadProjectData]);

  async function handleProjectChange(projectId: string): Promise<void> {
    setSelectedProjectId(projectId);
    setSelectedSourceId("");
    setLoadState("loading");
    setLoadError("");
    try {
      await loadProjectData(projectId, "");
    } catch (error: unknown) {
      setLoadError(error instanceof Error ? error.message : "The API catalog could not be loaded.");
      setLoadState("error");
    }
  }

  async function handleSourceFilter(sourceId: string): Promise<void> {
    setSelectedSourceId(sourceId);
    setLoadState("loading");
    setLoadError("");
    try {
      const catalogResponse = await getApiCatalog(
        selectedProjectId,
        sourceId || undefined,
      );
      setCatalog(catalogResponse);
      setSelectedOperationKey(
        catalogResponse.operations[0] ? operationKey(catalogResponse.operations[0]) : "",
      );
      setLoadState("ready");
    } catch (error: unknown) {
      setLoadError(error instanceof Error ? error.message : "The API catalog could not be loaded.");
      setLoadState("error");
    }
  }

  async function handleSynchronize(): Promise<void> {
    if (!selectedSource) {
      return;
    }
    setSyncState("running");
    setSyncError("");
    try {
      await synchronizeSource(selectedSource.id);
      const catalogResponse = await getApiCatalog(selectedProjectId, selectedSource.id);
      setCatalog(catalogResponse);
      setSelectedOperationKey(
        catalogResponse.operations[0] ? operationKey(catalogResponse.operations[0]) : "",
      );
    } catch (error: unknown) {
      setSyncError(error instanceof Error ? error.message : "The source could not be synchronized.");
    } finally {
      setSyncState("idle");
    }
  }

  const activeSources = sources.filter((source) => source.status === "READY");
  const latestRun = catalog.runs[0];

  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">Normalized technical catalog</p>
          <h1>API Catalog</h1>
        </div>
        <span className="environment-badge">Source-backed</span>
      </header>

      <section className="content-section" aria-labelledby="catalog-controls-title">
        <div className="section-heading">
          <div>
            <h2 id="catalog-controls-title">Catalog scope</h2>
            <p>Select a project and source. Synchronization creates a traceable catalog snapshot.</p>
          </div>
        </div>

        <div className="catalog-toolbar">
          <div className="field">
            <label htmlFor="catalog-project">Project</label>
            <select
              id="catalog-project"
              value={selectedProjectId}
              disabled={projects.length === 0}
              onChange={(event) => void handleProjectChange(event.target.value)}
            >
              {projects.length === 0 && <option value="">No projects available</option>}
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.key} — {project.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="catalog-source">Source</label>
            <select
              id="catalog-source"
              value={selectedSourceId}
              disabled={activeSources.length === 0}
              onChange={(event) => void handleSourceFilter(event.target.value)}
            >
              <option value="">All synchronized sources</option>
              {activeSources.map((source) => (
                <option key={source.id} value={source.id}>
                  {source.name}
                </option>
              ))}
            </select>
          </div>
          <div className="catalog-toolbar__action">
            <button
              type="button"
              className="button button--primary"
              disabled={!selectedSource || syncState === "running"}
              onClick={() => void handleSynchronize()}
            >
              {syncState === "running" ? "Synchronizing…" : "Synchronize source"}
            </button>
          </div>
        </div>

        {syncError && <p className="form-error" role="alert">{syncError}</p>}
        {loadState === "error" && <div className="notice notice--error" role="alert">{loadError}</div>}
        {loadState === "loading" && <p className="loading-state">Loading API catalog…</p>}
      </section>

      {loadState === "ready" && projects.length === 0 && (
        <section className="content-section">
          <div className="empty-state">
            <h2>Create a project first</h2>
            <p>The API catalog requires a project and an imported OpenAPI source.</p>
          </div>
        </section>
      )}

      {loadState === "ready" && projects.length > 0 && activeSources.length === 0 && (
        <section className="content-section">
          <div className="empty-state">
            <h2>Import an OpenAPI source</h2>
            <p>No active OpenAPI source is available for this project.</p>
          </div>
        </section>
      )}

      {loadState === "ready" && activeSources.length > 0 && catalog.operations.length === 0 && (
        <section className="content-section">
          <div className="empty-state">
            <h2>Synchronize a source</h2>
            <p>Select one source above, then create its first normalized catalog snapshot.</p>
          </div>
        </section>
      )}

      {catalog.operations.length > 0 && (
        <>
          <section className="content-section" aria-labelledby="operation-catalog-title">
            <div className="section-heading section-heading--split">
              <div>
                <h2 id="operation-catalog-title">Operations</h2>
                <p>
                  {latestRun
                    ? `Snapshot ${latestRun.id.slice(0, 8)} · ${latestRun.operation_count} operations · ${latestRun.schema_count} schemas`
                    : "Current operations from synchronized sources."}
                </p>
              </div>
              <span className="record-count">{catalog.operation_total} operations</span>
            </div>
            <div className="catalog-layout">
              <div className="table-frame">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Method</th>
                      <th scope="col">Path</th>
                      <th scope="col">Summary</th>
                      <th scope="col">Security</th>
                    </tr>
                  </thead>
                  <tbody>
                    {catalog.operations.map((operation) => (
                      <tr
                        key={operationKey(operation)}
                        className={
                          selectedOperation &&
                          operationKey(operation) === operationKey(selectedOperation)
                            ? "is-selected"
                            : undefined
                        }
                      >
                        <td><span className="http-method">{operation.method}</span></td>
                        <td>
                          <button
                            type="button"
                            className="catalog-row-button"
                            onClick={() => setSelectedOperationKey(operationKey(operation))}
                          >
                            <code>{operation.path}</code>
                          </button>
                        </td>
                        <td>{operation.summary || operation.operation_id || "No summary"}</td>
                        <td>{operation.security_schemes.join(", ") || "None declared"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {selectedOperation && <OperationEvidence operation={selectedOperation} />}
            </div>
          </section>

          <section className="content-section" aria-labelledby="schema-catalog-title">
            <div className="section-heading section-heading--split">
              <div>
                <h2 id="schema-catalog-title">Schemas</h2>
                <p>Component schemas are normalized with required fields and source pointers.</p>
              </div>
              <span className="record-count">{catalog.schema_total} schemas</span>
            </div>
            {catalog.schemas.length === 0 ? (
              <div className="empty-state"><p>No component schemas were declared.</p></div>
            ) : (
              <div className="table-frame">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Schema</th>
                      <th scope="col">Type</th>
                      <th scope="col">Properties</th>
                      <th scope="col">Evidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {catalog.schemas.map((schema) => (
                      <tr key={`${schema.source_id}:${schema.name}`}>
                        <td><strong>{schema.name}</strong></td>
                        <td>{schema.schema_type || "Not declared"}</td>
                        <td>{schema.properties.length}</td>
                        <td><code>{schema.source_pointer}</code></td>
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

function OperationEvidence({ operation }: { operation: ApiOperation }) {
  return (
    <aside className="evidence-panel" aria-label="Operation evidence">
      <span className="status-label">Selected operation</span>
      <h3>{operation.method} {operation.path}</h3>
      <dl className="evidence-list">
        <div><dt>Operation ID</dt><dd>{operation.operation_id || "Not declared"}</dd></div>
        <div><dt>Tags</dt><dd>{operation.tags.join(", ") || "None declared"}</dd></div>
        <div>
          <dt>Request</dt>
          <dd>
            {operation.request_body
              ? `${operation.request_body.media_types.join(", ") || "No media type"}${operation.request_body.required ? " · required" : ""}`
              : "No request body"}
          </dd>
        </div>
        <div>
          <dt>Responses</dt>
          <dd>{operation.responses.map((response) => response.status_code).join(", ") || "None declared"}</dd>
        </div>
        <div><dt>Parameters</dt><dd>{operation.parameters.length}</dd></div>
        <div><dt>Source</dt><dd><code>{operation.source_pointer}</code></dd></div>
      </dl>
    </aside>
  );
}

function operationKey(operation: ApiOperation): string {
  return `${operation.source_id}:${operation.method}:${operation.path}`;
}
