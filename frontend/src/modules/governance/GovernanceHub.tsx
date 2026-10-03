import { useEffect, useState } from "react";

import { listProjects } from "../projects/api";
import type { Project } from "../projects/types";
import { GovernanceWorkspace } from "./GovernanceWorkspace";

interface GovernanceHubProps {
  workspaceId: string | null;
}

export function GovernanceHub({ workspaceId }: GovernanceHubProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    if (workspaceId === null) {
      setProjects([]);
      setProjectId("");
      setState("ready");
      return () => controller.abort();
    }

    async function load(): Promise<void> {
      setState("loading");
      setError("");
      try {
        const collection = await listProjects(workspaceId, controller.signal);
        setProjects(collection.items);
        const firstActive = collection.items.find((project) => project.status === "ACTIVE") ?? collection.items[0];
        setProjectId((current) =>
          collection.items.some((project) => project.id === current)
            ? current
            : firstActive?.id ?? "",
        );
        setState("ready");
      } catch (loadError: unknown) {
        if (loadError instanceof DOMException && loadError.name === "AbortError") return;
        setError(loadError instanceof Error ? loadError.message : "Governance projects could not be loaded.");
        setState("error");
      }
    }

    void load();
    return () => controller.abort();
  }, [workspaceId]);

  if (workspaceId === null) {
    return (
      <section className="content-section project-workbench-state">
        <h1>Governance</h1>
        <p>Select a workspace before opening enterprise governance.</p>
      </section>
    );
  }

  if (state === "loading") {
    return <div className="project-workbench-state" role="status">Loading governance portfolio…</div>;
  }

  if (state === "error") {
    return <div className="notice notice--error" role="alert">{error}</div>;
  }

  if (projects.length === 0) {
    return (
      <section className="content-section project-workbench-state">
        <h1>Governance</h1>
        <p>Create a project first. Governance is scoped to a project and never invents portfolio facts.</p>
      </section>
    );
  }

  const selected = projects.find((project) => project.id === projectId) ?? projects[0];
  if (!selected) return null;

  return (
    <div className="governance-hub">
      <header className="topbar">
        <div>
          <p className="eyebrow">Enterprise control plane</p>
          <h1>Governance</h1>
          <p>Requirement traceability, change impact, and approval workflow from one workspace.</p>
        </div>
        <label className="field">
          <span>Project</span>
          <select value={selected.id} onChange={(event) => setProjectId(event.target.value)}>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>{project.key} — {project.name}</option>
            ))}
          </select>
        </label>
      </header>
      <GovernanceWorkspace project={selected} />
    </div>
  );
}
