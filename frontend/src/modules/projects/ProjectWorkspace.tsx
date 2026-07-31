import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { ApiClientError } from "../../shared/api/client";
import type { Workspace } from "../workspaces/types";
import { archiveProject, createProject, listProjects } from "./api";
import type { CreateProjectInput, OwnershipType, Project } from "./types";

const initialForm: CreateProjectInput = {
  key: "",
  name: "",
  description: "",
  ownership_type: "TEAM",
};

type LoadState = "loading" | "ready" | "error";

interface ProjectWorkspaceProps {
  workspace: Workspace;
  onOpenProject?: (project: Project) => void;
}

export function ProjectWorkspace({
  workspace,
  onOpenProject,
}: ProjectWorkspaceProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [loadError, setLoadError] = useState("");
  const [form, setForm] = useState<CreateProjectInput>(initialForm);
  const [formError, setFormError] = useState("");
  const [actionError, setActionError] = useState("");
  const [pendingArchiveId, setPendingArchiveId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isReadOnly = workspace.status === "ARCHIVED";

  const load = useCallback(
    async (signal?: AbortSignal): Promise<void> => {
      setLoadState("loading");
      setLoadError("");
      try {
        const response = await listProjects(workspace.id, signal);
        setProjects(response.items);
        setLoadState("ready");
      } catch (error: unknown) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setLoadError("Projects could not be loaded. Confirm that the backend is running.");
        setLoadState("error");
      }
    },
    [workspace.id],
  );

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const activeProjects = useMemo(
    () => projects.filter((project) => project.status === "ACTIVE").length,
    [projects],
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (isReadOnly) {
      return;
    }
    setFormError("");
    setIsSubmitting(true);
    try {
      const created = await createProject(workspace.id, form);
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
    if (isReadOnly || project.status === "ARCHIVED") {
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
          <p className="eyebrow">{workspace.name}</p>
          <h1>Projects</h1>
          <p className="page-summary">
            Projects group features, sources, requirements, documents, and releases inside this workspace.
          </p>
        </div>
        <span
          className={
            workspace.status === "ACTIVE"
              ? "environment-badge environment-badge--success"
              : "environment-badge environment-badge--warning"
          }
        >
          {workspace.key} · {workspace.status === "ACTIVE" ? "Active" : "Archived"}
        </span>
      </header>

      {isReadOnly && (
        <div className="notice notice--warning" role="status">
          <span>This workspace is archived. Existing project evidence remains read-only.</span>
        </div>
      )}

      <section className="content-section" aria-labelledby="projects-title">
        <div className="section-heading section-heading--split">
          <div>
            <h2 id="projects-title">Project registry</h2>
            <p>Only projects assigned to {workspace.name} are shown here.</p>
          </div>
          <span className="record-count">
            {activeProjects} active · {projects.length} total
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
            <h3>No projects in this workspace</h3>
            <p>Create the first project for {workspace.name}.</p>
          </div>
        )}

        {projects.length > 0 && (
          <div className="table-frame">
            <table>
              <thead>
                <tr>
                  <th scope="col">Project</th>
                  <th scope="col">Key</th>
                  <th scope="col">Ownership</th>
                  <th scope="col">Status</th>
                  <th scope="col" className="table-action-column">Action</th>
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
                    <td><code>{project.key}</code></td>
                    <td>{formatOwnership(project)}</td>
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
                      <span className="project-row-actions">
                        <button
                          type="button"
                          className="button button--secondary"
                          aria-label={`Open ${project.name} workbench`}
                          disabled={project.status === "ARCHIVED" || onOpenProject === undefined}
                          onClick={() => onOpenProject?.(project)}
                        >
                          Open workbench
                        </button>
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
                            disabled={isReadOnly || project.status === "ARCHIVED"}
                            onClick={() => setPendingArchiveId(project.id)}
                          >
                            {project.status === "ARCHIVED" ? "Archived" : "Archive"}
                          </button>
                        )}
                      </span>
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
            <p>The project will be assigned to {workspace.name}.</p>
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
                value={form.name}
                disabled={isReadOnly}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                placeholder="ERP Core"
              />
              <small>Human-readable system or application name.</small>
            </div>

            <div className="field">
              <label htmlFor="project-key">Project key</label>
              <input
                id="project-key"
                required
                minLength={2}
                maxLength={20}
                pattern="[A-Za-z][A-Za-z0-9-]+"
                value={form.key}
                disabled={isReadOnly}
                onChange={(event) => setForm({ ...form, key: event.target.value.toUpperCase() })}
                placeholder="ERP-CORE"
              />
              <small>2-20 letters, numbers, or hyphens. Stored in uppercase.</small>
            </div>

            <div className="field">
              <label htmlFor="ownership-type">Ownership</label>
              <select
                id="ownership-type"
                value={form.ownership_type}
                disabled={isReadOnly}
                onChange={(event) =>
                  setForm({
                    ...form,
                    ownership_type: event.target.value as OwnershipType,
                  })
                }
              >
                <option value="TEAM">Team</option>
                <option value="PERSONAL">Personal</option>
              </select>
              <small>Governance ownership; access control will be implemented separately.</small>
            </div>

            <div className="field field--wide">
              <label htmlFor="project-description">Description</label>
              <textarea
                id="project-description"
                maxLength={500}
                rows={3}
                value={form.description}
                disabled={isReadOnly}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
                placeholder="Describe the product, system, or application boundary."
              />
              <small>{form.description.length}/500 characters</small>
            </div>
          </div>

          {formError && <p className="form-error" role="alert">{formError}</p>}

          <div className="form-actions">
            <button
              type="submit"
              className="button button--primary"
              disabled={isSubmitting || isReadOnly}
            >
              {isSubmitting ? "Creating…" : "Create project"}
            </button>
          </div>
        </form>
      </section>
    </>
  );
}

function formatOwnership(project: Project): string {
  if (project.ownership_type !== undefined) {
    return project.ownership_type === "PERSONAL" ? "Personal" : "Team";
  }
  return project.workspace_type === "ENTERPRISE" ? "Team" : "Personal";
}

function formatStatus(value: Project["status"]): string {
  return value.charAt(0) + value.slice(1).toLowerCase();
}
