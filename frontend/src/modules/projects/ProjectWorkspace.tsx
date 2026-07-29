import { type FormEvent, useCallback, useEffect, useState } from "react";

import { ApiClientError } from "../../shared/api/client";
import { archiveProject, createProject, listProjects } from "./api";
import type { CreateProjectInput, Project, WorkspaceType } from "./types";

const initialForm: CreateProjectInput = {
  key: "",
  name: "",
  description: "",
  workspace_type: "PERSONAL",
};

type LoadState = "loading" | "ready" | "error";

export function ProjectWorkspace() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [loadError, setLoadError] = useState("");
  const [form, setForm] = useState<CreateProjectInput>(initialForm);
  const [formError, setFormError] = useState("");
  const [actionError, setActionError] = useState("");
  const [pendingArchiveId, setPendingArchiveId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const load = useCallback(async (signal?: AbortSignal): Promise<void> => {
    setLoadState("loading");
    setLoadError("");
    try {
      const response = await listProjects(signal);
      setProjects(response.items);
      setLoadState("ready");
    } catch (error: unknown) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      setLoadError("Projects could not be loaded. Confirm that the backend is running.");
      setLoadState("error");
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setFormError("");
    setIsSubmitting(true);
    try {
      const created = await createProject(form);
      setProjects((current) => [created, ...current]);
      setForm(initialForm);
    } catch (error: unknown) {
      setFormError(
        error instanceof ApiClientError ? error.message : "The project could not be created.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleArchive(project: Project): Promise<void> {
    if (project.status === "ARCHIVED") {
      return;
    }
    setActionError("");
    try {
      const archived = await archiveProject(project.id);
      setProjects((current) =>
        current.map((item) => (item.id === archived.id ? archived : item)),
      );
      setPendingArchiveId(null);
    } catch (error: unknown) {
      setActionError(
        error instanceof ApiClientError ? error.message : "The project could not be archived.",
      );
    }
  }

  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">Workspace administration</p>
          <h1>Projects</h1>
        </div>
        <span className="environment-badge">Local development</span>
      </header>

      <section className="content-section" aria-labelledby="projects-title">
        <div className="section-heading section-heading--split">
          <div>
            <h2 id="projects-title">Project registry</h2>
            <p>Projects provide the boundary for sources, catalogs, changes, and documents.</p>
          </div>
          <span
            className="record-count"
            aria-label={`${projects.length} ${projects.length === 1 ? "project" : "projects"}`}
          >
            {projects.length} {projects.length === 1 ? "project" : "projects"}
          </span>
        </div>

        {loadState === "error" && (
          <div className="notice notice--error" role="alert">
            <span>{loadError}</span>
            <button type="button" className="button button--secondary" onClick={() => void load()}>
              Retry
            </button>
          </div>
        )}

        {actionError && (
          <div className="notice notice--error" role="alert">
            <span>{actionError}</span>
          </div>
        )}

        {loadState === "loading" && <p className="loading-state">Loading projects…</p>}

        {loadState === "ready" && projects.length === 0 && (
          <div className="empty-state">
            <h3>No projects yet</h3>
            <p>Create the first project to establish a source and documentation boundary.</p>
          </div>
        )}

        {projects.length > 0 && (
          <div className="table-frame">
            <table>
              <thead>
                <tr>
                  <th scope="col">Project</th>
                  <th scope="col">Key</th>
                  <th scope="col">Workspace</th>
                  <th scope="col">Status</th>
                  <th scope="col" className="table-action-column">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody>
                {projects.map((project) => (
                  <tr key={project.id}>
                    <td>
                      <strong>{project.name}</strong>
                      <span className="table-secondary-text">
                        {project.description || "No description provided"}
                      </span>
                    </td>
                    <td>
                      <code>{project.key}</code>
                    </td>
                    <td>{formatWorkspace(project.workspace_type)}</td>
                    <td>
                      <span
                        className={
                          project.status === "ACTIVE"
                            ? "status-indicator status-indicator--success"
                            : "status-indicator status-indicator--neutral"
                        }
                      >
                        {formatStatus(project.status)}
                      </span>
                    </td>
                    <td className="table-action-column">
                      {pendingArchiveId === project.id ? (
                        <span className="inline-actions">
                          <button
                            type="button"
                            className="button button--danger-quiet"
                            onClick={() => void handleArchive(project)}
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
                          disabled={project.status === "ARCHIVED"}
                          onClick={() => setPendingArchiveId(project.id)}
                        >
                          {project.status === "ARCHIVED" ? "Archived" : "Archive"}
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

      <section className="content-section" aria-labelledby="create-project-title">
        <div className="section-heading">
          <div>
            <h2 id="create-project-title">Create project</h2>
            <p>Use a stable key because future sources and documents will reference it.</p>
          </div>
        </div>

        <form className="form-panel" onSubmit={(event) => void handleSubmit(event)}>
          <div className="form-grid">
            <div className="field">
              <label htmlFor="project-name">Project name</label>
              <input
                id="project-name"
                required
                minLength={3}
                maxLength={80}
                aria-describedby="project-name-help"
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                placeholder="Commerce Documentation"
              />
              <small id="project-name-help">Human-readable name shown across the workspace.</small>
            </div>

            <div className="field">
              <label htmlFor="project-key">Project key</label>
              <input
                id="project-key"
                required
                minLength={2}
                maxLength={20}
                pattern="[A-Za-z][A-Za-z0-9-]+"
                aria-describedby="project-key-help"
                value={form.key}
                onChange={(event) => setForm({ ...form, key: event.target.value.toUpperCase() })}
                placeholder="COMMERCE"
              />
              <small id="project-key-help">
                2-20 letters, numbers, or hyphens. Stored in uppercase.
              </small>
            </div>

            <div className="field">
              <label htmlFor="workspace-type">Workspace type</label>
              <select
                id="workspace-type"
                aria-describedby="workspace-type-help"
                value={form.workspace_type}
                onChange={(event) =>
                  setForm({ ...form, workspace_type: event.target.value as WorkspaceType })
                }
              >
                <option value="PERSONAL">Personal</option>
                <option value="DEMO">Demo</option>
                <option value="ENTERPRISE">Enterprise</option>
              </select>
              <small id="workspace-type-help">
                Defines the intended governance context; it does not grant access.
              </small>
            </div>

            <div className="field field--wide">
              <label htmlFor="project-description">Description</label>
              <textarea
                id="project-description"
                maxLength={500}
                rows={3}
                aria-describedby="project-description-help"
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
                placeholder="Describe the system or documentation scope."
              />
              <small id="project-description-help">{form.description.length}/500 characters</small>
            </div>
          </div>

          {formError && (
            <p className="form-error" role="alert">
              {formError}
            </p>
          )}

          <div className="form-actions">
            <button type="submit" className="button button--primary" disabled={isSubmitting}>
              {isSubmitting ? "Creating…" : "Create project"}
            </button>
          </div>
        </form>
      </section>
    </>
  );
}

function formatWorkspace(value: WorkspaceType): string {
  return value.charAt(0) + value.slice(1).toLowerCase();
}

function formatStatus(value: Project["status"]): string {
  return value.charAt(0) + value.slice(1).toLowerCase();
}
