import { type FormEvent, useCallback, useEffect, useState } from "react";

import { ApiClientError } from "../../shared/api/client";
import { Icon } from "../../shared/ui/Icon";
import { archiveWorkspace, createWorkspace, listWorkspaces } from "./api";
import type { CreateWorkspaceInput, Workspace } from "./types";

const initialForm: CreateWorkspaceInput = {
  key: "",
  name: "",
  description: "",
};

interface WorkspaceRegistryProps {
  activeWorkspaceId: string | null;
  onSelectWorkspace: (workspace: Workspace) => void;
  onWorkspacesChanged: (workspaces: Workspace[]) => void;
}

export function WorkspaceRegistry({
  activeWorkspaceId,
  onSelectWorkspace,
  onWorkspacesChanged,
}: WorkspaceRegistryProps) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loadState, setLoadState] = useState<"loading" | "ready" | "error">("loading");
  const [loadError, setLoadError] = useState("");
  const [form, setForm] = useState<CreateWorkspaceInput>(initialForm);
  const [formError, setFormError] = useState("");
  const [actionError, setActionError] = useState("");
  const [pendingArchiveId, setPendingArchiveId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const publish = useCallback(
    (items: Workspace[]): void => {
      setWorkspaces(items);
      onWorkspacesChanged(items);
    },
    [onWorkspacesChanged],
  );

  const load = useCallback(
    async (signal?: AbortSignal): Promise<void> => {
      setLoadState("loading");
      setLoadError("");
      try {
        const response = await listWorkspaces(signal);
        publish(response.items);
        setLoadState("ready");
      } catch (error: unknown) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setLoadError("Workspaces could not be loaded. Confirm that the backend is running.");
        setLoadState("error");
      }
    },
    [publish],
  );

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
      const created = await createWorkspace(form);
      const next = [...workspaces, created];
      publish(next);
      setForm(initialForm);
      onSelectWorkspace(created);
    } catch (error: unknown) {
      setFormError(
        error instanceof ApiClientError ? error.message : "The workspace could not be created.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleArchive(workspace: Workspace): Promise<void> {
    if (workspace.status === "ARCHIVED") {
      return;
    }
    setActionError("");
    try {
      const archived = await archiveWorkspace(workspace.id);
      publish(
        workspaces.map((item) => (item.id === archived.id ? archived : item)),
      );
      setPendingArchiveId(null);
    } catch (error: unknown) {
      setActionError(
        error instanceof ApiClientError ? error.message : "The workspace could not be archived.",
      );
    }
  }

  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">Platform administration</p>
          <h1>Workspaces</h1>
          <p className="page-summary">
            Workspaces separate systems, projects, templates, policies, and release governance.
          </p>
        </div>
        <span className="environment-badge">Workspace foundation</span>
      </header>

      <section className="content-section" aria-labelledby="workspace-registry-title">
        <div className="section-heading section-heading--split">
          <div>
            <h2 id="workspace-registry-title">Workspace registry</h2>
            <p>Select the operational boundary before opening its projects.</p>
          </div>
          <span className="record-count">
            {workspaces.length} {workspaces.length === 1 ? "workspace" : "workspaces"}
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
        {loadState === "loading" && <p className="loading-state">Loading workspaces…</p>}

        {loadState === "ready" && workspaces.length === 0 && (
          <div className="empty-state">
            <h3>No workspaces yet</h3>
            <p>Create the first workspace before creating projects.</p>
          </div>
        )}

        {workspaces.length > 0 && (
          <div className="table-frame">
            <table>
              <thead>
                <tr>
                  <th scope="col">Workspace</th>
                  <th scope="col">Key</th>
                  <th scope="col">Status</th>
                  <th scope="col" className="table-action-column">Action</th>
                </tr>
              </thead>
              <tbody>
                {workspaces.map((workspace) => (
                  <tr
                    key={workspace.id}
                    className={workspace.id === activeWorkspaceId ? "is-selected" : undefined}
                  >
                    <td>
                      <strong>{workspace.name}</strong>
                      <span className="table-secondary-text">
                        {workspace.description || "No description provided"}
                      </span>
                    </td>
                    <td><code>{workspace.key}</code></td>
                    <td>
                      <span
                        className={
                          workspace.status === "ACTIVE"
                            ? "status-indicator status-indicator--success"
                            : "status-indicator status-indicator--neutral"
                        }
                      >
                        {workspace.status === "ACTIVE" ? "Active" : "Archived"}
                      </span>
                    </td>
                    <td className="table-action-column">
                      <span className="project-row-actions">
                        <button
                          type="button"
                          className="button button--secondary"
                          onClick={() => onSelectWorkspace(workspace)}
                        >
                          <Icon name="arrow-right" size={14} />
                          {workspace.status === "ARCHIVED" ? "View workspace" : "Open workspace"}
                        </button>
                        {pendingArchiveId === workspace.id ? (
                          <span className="inline-actions">
                            <button
                              type="button"
                              className="button button--danger-quiet"
                              onClick={() => void handleArchive(workspace)}
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
                            disabled={
                              workspace.status === "ARCHIVED" || workspace.key === "GENERAL"
                            }
                            onClick={() => setPendingArchiveId(workspace.id)}
                          >
                            {workspace.status === "ARCHIVED" ? "Archived" : "Archive"}
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

      <section className="content-section" aria-labelledby="create-workspace-title">
        <div className="section-heading">
          <div>
            <h2 id="create-workspace-title">Create workspace</h2>
            <p>Use a stable key for routes, governance policies, and future template scopes.</p>
          </div>
        </div>

        <form className="form-panel" onSubmit={(event) => void handleSubmit(event)}>
          <div className="form-grid">
            <div className="field">
              <label htmlFor="workspace-name">Workspace name</label>
              <input
                id="workspace-name"
                required
                minLength={3}
                maxLength={80}
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                placeholder="ERP Workspace"
              />
            </div>
            <div className="field">
              <label htmlFor="workspace-key">Workspace key</label>
              <input
                id="workspace-key"
                required
                minLength={2}
                maxLength={20}
                pattern="[A-Za-z][A-Za-z0-9-]+"
                value={form.key}
                onChange={(event) =>
                  setForm({ ...form, key: event.target.value.toUpperCase() })
                }
                placeholder="ERP"
              />
            </div>
            <div className="field field--wide">
              <label htmlFor="workspace-description">Description</label>
              <textarea
                id="workspace-description"
                maxLength={500}
                rows={3}
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
                placeholder="Systems, projects, and documentation governed within this workspace."
              />
              <small>{form.description.length}/500 characters</small>
            </div>
          </div>

          {formError && <p className="form-error" role="alert">{formError}</p>}

          <div className="form-actions">
            <button type="submit" className="button button--primary" disabled={isSubmitting}>
              {isSubmitting ? "Creating…" : "Create workspace"}
            </button>
          </div>
        </form>
      </section>
    </>
  );
}
