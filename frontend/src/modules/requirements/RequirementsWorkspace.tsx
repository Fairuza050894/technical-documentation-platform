import { useCallback, useEffect, useMemo, useState } from "react";

import type { Project } from "../projects/types";
import {
  createRequirement,
  createRequirementWorkflowItem,
  getProjectTraceability,
  listRequirements,
  listWorkflowItems,
  transitionRequirement,
} from "./api";
import type {
  ProjectTraceability,
  Requirement,
  RequirementType,
  WorkflowItem,
} from "./types";

interface RequirementsWorkspaceProps {
  workspaceId: string;
  project: Project;
}

const requirementTypes: Array<{ value: RequirementType; label: string }> = [
  { value: "BUSINESS", label: "Business" },
  { value: "SYSTEM", label: "System" },
  { value: "FUNCTIONAL", label: "Functional" },
  { value: "NON_FUNCTIONAL", label: "Non-functional" },
  { value: "COMPLIANCE", label: "Compliance" },
];

export function RequirementsWorkspace({ workspaceId, project }: RequirementsWorkspaceProps) {
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [traceability, setTraceability] = useState<ProjectTraceability>({ items: [], total: 0 });
  const [workflowItems, setWorkflowItems] = useState<WorkflowItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [key, setKey] = useState("");
  const [type, setType] = useState<RequirementType>("FUNCTIONAL");
  const [title, setTitle] = useState("");
  const [statement, setStatement] = useState("");
  const [criterion, setCriterion] = useState("");

  const load = useCallback(async (signal?: AbortSignal) => {
    const [requirementResult, traceabilityResult, workflowResult] = await Promise.all([
      listRequirements(workspaceId, project.id, signal),
      getProjectTraceability(workspaceId, project.id, signal),
      listWorkflowItems(workspaceId, project.id, signal),
    ]);
    setRequirements(requirementResult.items);
    setTraceability(traceabilityResult);
    setWorkflowItems(workflowResult.items);
    setSelectedId((current) => current ?? requirementResult.items[0]?.id ?? null);
  }, [project.id, workspaceId]);

  useEffect(() => {
    const controller = new AbortController();
    setError("");
    void load(controller.signal).catch((reason: unknown) => {
      if (!controller.signal.aborted) {
        setError(reason instanceof Error ? reason.message : "Could not load requirements governance.");
      }
    });
    return () => controller.abort();
  }, [load]);

  const selected = requirements.find((item) => item.id === selectedId) ?? null;
  const selectedTrace = traceability.items.find((item) => item.requirement.id === selectedId) ?? null;
  const openWork = workflowItems.filter(
    (item) => item.state !== "CLOSED" && item.state !== "CANCELLED",
  );
  const approved = requirements.filter((item) => item.status === "APPROVED").length;
  const fullyTraced = traceability.items.filter((item) =>
    Object.values(item.coverage).every(Boolean),
  ).length;

  const coverageEntries = useMemo(
    () => selectedTrace ? Object.entries(selectedTrace.coverage) : [],
    [selectedTrace],
  );

  async function handleCreate() {
    if (!key.trim() || !title.trim() || statement.trim().length < 10 || !criterion.trim()) {
      setError("Key, title, statement, and at least one acceptance criterion are required.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const created = await createRequirement(workspaceId, project.id, {
        key: key.trim(),
        requirement_type: type,
        title: title.trim(),
        statement: statement.trim(),
        acceptance_criteria: [criterion.trim()],
        rationale: "",
        feature_id: null,
      });
      setShowCreate(false);
      setKey("");
      setTitle("");
      setStatement("");
      setCriterion("");
      await load();
      setSelectedId(created.id);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not create requirement.");
    } finally {
      setBusy(false);
    }
  }

  async function handleTransition(action: "APPROVE" | "RETIRE") {
    if (!selected) return;
    setBusy(true);
    setError("");
    try {
      await transitionRequirement(workspaceId, project.id, selected.id, action);
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not update requirement state.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateWorkItem() {
    if (!selected) return;
    setBusy(true);
    setError("");
    try {
      await createRequirementWorkflowItem(workspaceId, project.id, selected);
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not create review work item.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="requirements-workspace" aria-labelledby="requirements-title">
      <header className="requirements-workspace__header">
        <div>
          <p className="eyebrow">Governed product intent</p>
          <h2 id="requirements-title">Requirements & traceability</h2>
          <p>
            Capture approved intent before prose, link it to evidence and verification, then drive
            accountable review work from the same project boundary.
          </p>
        </div>
        <button className="button button--primary" type="button" onClick={() => setShowCreate(true)}>
          New requirement
        </button>
      </header>

      <div className="requirements-kpis" aria-label="Requirements governance summary">
        <Metric label="Requirements" value={requirements.length} />
        <Metric label="Approved" value={approved} />
        <Metric label="Fully traced" value={fullyTraced} />
        <Metric label="Open work" value={openWork.length} attention={openWork.some((item) => item.overdue)} />
      </div>

      {error ? <p className="error-state" role="alert">{error}</p> : null}

      {showCreate ? (
        <div className="requirements-create-panel">
          <div className="form-grid">
            <label className="field">
              <span>Requirement key</span>
              <input value={key} onChange={(event) => setKey(event.target.value)} placeholder="REQ-SHIPMENT-001" />
            </label>
            <label className="field">
              <span>Type</span>
              <select value={type} onChange={(event) => setType(event.target.value as RequirementType)}>
                {requirementTypes.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
              </select>
            </label>
            <label className="field field--wide">
              <span>Title</span>
              <input value={title} onChange={(event) => setTitle(event.target.value)} />
            </label>
            <label className="field field--wide">
              <span>Requirement statement</span>
              <textarea value={statement} onChange={(event) => setStatement(event.target.value)} />
            </label>
            <label className="field field--wide">
              <span>Acceptance criterion</span>
              <textarea value={criterion} onChange={(event) => setCriterion(event.target.value)} />
            </label>
          </div>
          <div className="form-actions">
            <button className="button" type="button" onClick={() => setShowCreate(false)}>Cancel</button>
            <button className="button button--primary" type="button" disabled={busy} onClick={() => void handleCreate()}>
              Create draft
            </button>
          </div>
        </div>
      ) : null}

      <div className="requirements-layout">
        <div className="requirements-registry" aria-label="Requirement registry">
          <div className="section-heading">
            <div>
              <h3>Registry</h3>
              <p>Immutable revision history is retained whenever intent changes.</p>
            </div>
          </div>
          {requirements.length === 0 ? (
            <p className="empty-state">No requirements yet. Start with the business or system intent that must be verified.</p>
          ) : requirements.map((item) => (
            <button
              className={`requirement-row${item.id === selectedId ? " requirement-row--selected" : ""}`}
              key={item.id}
              type="button"
              onClick={() => setSelectedId(item.id)}
            >
              <span>
                <strong>{item.key}</strong>
                <small>{item.requirement_type.replaceAll("_", " ")}</small>
              </span>
              <span className={`status-badge status-badge--${item.status.toLowerCase()}`}>{item.status.replaceAll("_", " ")}</span>
              <span className="requirement-row__title">{item.title}</span>
              <small>rev {item.revision}</small>
            </button>
          ))}
        </div>

        <aside className="requirements-detail" aria-label="Selected requirement governance">
          {selected ? (
            <>
              <div className="requirements-detail__heading">
                <div>
                  <p className="eyebrow">{selected.key} · rev {selected.revision}</p>
                  <h3>{selected.title}</h3>
                </div>
                <span className={`status-badge status-badge--${selected.status.toLowerCase()}`}>{selected.status.replaceAll("_", " ")}</span>
              </div>
              <p>{selected.statement}</p>
              <div className="traceability-coverage">
                <h4>Traceability coverage</h4>
                <div className="traceability-coverage__grid">
                  {coverageEntries.map(([label, covered]) => (
                    <span className={covered ? "trace-chip trace-chip--covered" : "trace-chip"} key={label}>
                      {covered ? "✓" : "○"} {label}
                    </span>
                  ))}
                </div>
                <p className="helper-text">Missing links stay explicit; TDP does not infer official traceability.</p>
              </div>
              <div className="requirements-actions">
                {selected.status === "DRAFT" ? (
                  <button className="button button--primary" type="button" disabled={busy} onClick={() => void handleTransition("APPROVE")}>Approve requirement</button>
                ) : null}
                {selected.status !== "RETIRED" ? (
                  <button className="button" type="button" disabled={busy} onClick={() => void handleTransition("RETIRE")}>Retire</button>
                ) : null}
                <button className="button" type="button" disabled={busy} onClick={() => void handleCreateWorkItem()}>Create review work item</button>
              </div>
            </>
          ) : <p className="empty-state">Select a requirement to inspect governance and traceability.</p>}
        </aside>
      </div>

      <div className="workflow-queue">
        <div className="section-heading"><div><h3>Governed work queue</h3><p>Human work items use explicit state transitions and priority-based SLA targets.</p></div></div>
        {openWork.length === 0 ? <p className="empty-state">No open requirement work items.</p> : (
          <div className="workflow-queue__list">
            {openWork.map((item) => (
              <article className={`workflow-card${item.overdue ? " workflow-card--overdue" : ""}`} key={item.id}>
                <div><strong>{item.title}</strong><p>{item.entity_type.replaceAll("_", " ")} · {item.state.replaceAll("_", " ")}</p></div>
                <span className="workflow-card__priority">{item.priority}</span>
                <small>Due {new Date(item.due_at).toLocaleString()}</small>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function Metric({ label, value, attention = false }: { label: string; value: number; attention?: boolean }) {
  return <article className={`requirements-kpi${attention ? " requirements-kpi--attention" : ""}`}><span>{label}</span><strong>{value}</strong></article>;
}
