import { FormEvent, useCallback, useEffect, useState } from "react";

import type { Project } from "../projects/types";
import {
  createImpactAssessment,
  createRequirement,
  createTraceLink,
  createWorkflowCase,
  getGovernanceSummary,
  transitionWorkflowCase,
} from "./api";
import type {
  ChangeSurface,
  GovernanceSummary,
  RequirementType,
  TraceTargetType,
  WorkflowState,
} from "./types";

interface GovernanceWorkspaceProps {
  project: Project;
}

type LoadState = "loading" | "ready" | "error";

const nextState: Partial<Record<WorkflowState, WorkflowState>> = {
  OPEN: "ANALYSIS",
  ANALYSIS: "UPDATE_REQUIRED",
  UPDATE_REQUIRED: "IN_REVIEW",
  IN_REVIEW: "APPROVED",
  APPROVED: "RELEASED",
  REJECTED: "ANALYSIS",
};

export function GovernanceWorkspace({ project }: GovernanceWorkspaceProps) {
  const [summary, setSummary] = useState<GovernanceSummary | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async (signal?: AbortSignal) => {
    setLoadState("loading");
    setError("");
    try {
      setSummary(await getGovernanceSummary(project.id, signal));
      setLoadState("ready");
    } catch (loadError: unknown) {
      if (loadError instanceof DOMException && loadError.name === "AbortError") return;
      setError(loadError instanceof Error ? loadError.message : "Governance data could not be loaded.");
      setLoadState("error");
    }
  }, [project.id]);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  async function run(action: () => Promise<unknown>): Promise<void> {
    setBusy(true);
    setError("");
    try {
      await action();
      await load();
    } catch (actionError: unknown) {
      setError(actionError instanceof Error ? actionError.message : "Governance action failed.");
    } finally {
      setBusy(false);
    }
  }

  if (loadState === "loading" && summary === null) {
    return <div className="project-workbench-state" role="status">Loading governance chain…</div>;
  }

  if (loadState === "error" && summary === null) {
    return <div className="notice notice--error" role="alert">{error}</div>;
  }

  if (summary === null) return null;

  return (
    <div className="governance-workspace">
      <section className="content-section" aria-labelledby="governance-title">
        <div className="section-heading">
          <div>
            <p className="section-kicker">Enterprise governance chain</p>
            <h2 id="governance-title">Requirements, traceability, impact, and workflow</h2>
            <p>
              Govern changes from intent to release without turning inferred data into official facts.
            </p>
          </div>
        </div>

        {error && <div className="notice notice--error" role="alert">{error}</div>}

        <div className="project-summary-grid" aria-label="Governance health">
          <Metric label="Requirements" value={summary.requirement_total} detail={`${summary.linked_requirement_total} linked`} />
          <Metric label="Traceability" value={`${summary.coverage_percent}%`} detail="requirements with at least one governed link" />
          <Metric label="Impact decisions" value={summary.impact_total} detail="deterministic assessments" />
          <Metric label="Open workflow" value={summary.open_workflow_total} detail="cases requiring human action" />
        </div>
      </section>

      <RequirementSection projectId={project.id} summary={summary} busy={busy} run={run} />
      <ImpactSection projectId={project.id} summary={summary} busy={busy} run={run} />
      <WorkflowSection summary={summary} busy={busy} run={run} />
    </div>
  );
}

function Metric({ label, value, detail }: { label: string; value: string | number; detail: string }) {
  return (
    <article className="summary-card">
      <span className="summary-card__label">{label}</span>
      <strong className="summary-card__value">{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

function RequirementSection({
  projectId,
  summary,
  busy,
  run,
}: {
  projectId: string;
  summary: GovernanceSummary;
  busy: boolean;
  run: (action: () => Promise<unknown>) => Promise<void>;
}) {
  const [type, setType] = useState<RequirementType>("SYSTEM");
  const [title, setTitle] = useState("");
  const [statement, setStatement] = useState("");
  const [rationale, setRationale] = useState("");
  const [targetType, setTargetType] = useState<TraceTargetType>("EVIDENCE");
  const [targetId, setTargetId] = useState("");

  async function submitRequirement(event: FormEvent): Promise<void> {
    event.preventDefault();
    await run(() => createRequirement(projectId, {
      requirement_type: type,
      title,
      statement,
      rationale,
    }));
    setTitle("");
    setStatement("");
    setRationale("");
  }

  const firstUnlinked = summary.requirements.find(
    (requirement) => !summary.trace_links.some((link) => link.requirement_id === requirement.requirement_id),
  );

  async function linkRequirement(event: FormEvent): Promise<void> {
    event.preventDefault();
    if (!firstUnlinked) return;
    await run(() => createTraceLink(projectId, {
      requirement_id: firstUnlinked.requirement_id,
      target_type: targetType,
      target_id: targetId,
      relation: "VERIFIED_BY",
    }));
    setTargetId("");
  }

  return (
    <section className="content-section" aria-labelledby="requirements-title">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Requirement Registry</p>
          <h2 id="requirements-title">Immutable requirement revisions</h2>
        </div>
      </div>

      {summary.requirements.length === 0 ? (
        <p className="empty-state">No governed requirements yet. Add the first requirement below.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Requirement</th><th>Type</th><th>Revision</th><th>Status</th><th>Trace links</th></tr></thead>
            <tbody>
              {summary.requirements.map((item) => (
                <tr key={item.requirement_id}>
                  <td><strong>{item.title}</strong><br /><small>{item.statement}</small></td>
                  <td>{item.requirement_type.replace("_", " ")}</td>
                  <td>v{item.revision}</td>
                  <td>{item.status}</td>
                  <td>{summary.trace_links.filter((link) => link.requirement_id === item.requirement_id).length}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <details className="form-panel">
        <summary>Add governed requirement</summary>
        <form onSubmit={(event) => void submitRequirement(event)} className="form-grid">
          <label className="field">Type<select value={type} onChange={(event) => setType(event.target.value as RequirementType)}><option value="BUSINESS">Business</option><option value="SYSTEM">System</option><option value="NON_FUNCTIONAL">Non-functional</option></select></label>
          <label className="field field--wide">Title<input value={title} onChange={(event) => setTitle(event.target.value)} required minLength={3} /></label>
          <label className="field field--wide">Requirement<textarea value={statement} onChange={(event) => setStatement(event.target.value)} required minLength={3} /></label>
          <label className="field field--wide">Rationale<textarea value={rationale} onChange={(event) => setRationale(event.target.value)} required minLength={3} /></label>
          <div className="form-actions"><button className="button button--primary" type="submit" disabled={busy}>Create requirement</button></div>
        </form>
      </details>

      {firstUnlinked && (
        <details className="form-panel">
          <summary>Link next untraced requirement</summary>
          <form onSubmit={(event) => void linkRequirement(event)} className="form-grid">
            <p className="field field--wide"><strong>{firstUnlinked.title}</strong><br /><small>{firstUnlinked.requirement_id}</small></p>
            <label className="field">Target<select value={targetType} onChange={(event) => setTargetType(event.target.value as TraceTargetType)}><option value="FEATURE">Feature</option><option value="EVIDENCE">Evidence</option><option value="TEST">Test</option><option value="DOCUMENT">Document</option><option value="RELEASE">Release</option><option value="SOURCE">Source</option></select></label>
            <label className="field">Target reference<input value={targetId} onChange={(event) => setTargetId(event.target.value)} required /></label>
            <div className="form-actions"><button className="button button--secondary" type="submit" disabled={busy}>Create trace link</button></div>
          </form>
        </details>
      )}
    </section>
  );
}

function ImpactSection({ projectId, summary, busy, run }: { projectId: string; summary: GovernanceSummary; busy: boolean; run: (action: () => Promise<unknown>) => Promise<void> }) {
  const [surface, setSurface] = useState<ChangeSurface>("API");
  const [reference, setReference] = useState("");

  async function submit(event: FormEvent): Promise<void> {
    event.preventDefault();
    await run(() => createImpactAssessment(projectId, { change_reference: reference, surface }));
    setReference("");
  }

  return (
    <section className="content-section" aria-labelledby="impact-title">
      <div className="section-heading"><div><p className="section-kicker">Change Impact</p><h2 id="impact-title">Deterministic impact decisions</h2><p>Impact targets come from policy, not free-form AI inference.</p></div></div>
      {summary.impact_assessments.length > 0 && (
        <div className="table-wrap"><table><thead><tr><th>Change</th><th>Surface</th><th>Affected control areas</th></tr></thead><tbody>{summary.impact_assessments.map((item) => <tr key={item.id}><td>{item.change_reference}</td><td>{item.surface}</td><td>{item.affected_targets.join(", ")}</td></tr>)}</tbody></table></div>
      )}
      <details className="form-panel"><summary>Assess a change</summary><form onSubmit={(event) => void submit(event)} className="form-grid"><label className="field">Surface<select value={surface} onChange={(event) => setSurface(event.target.value as ChangeSurface)}><option value="API">API</option><option value="SCHEMA">Schema</option><option value="REPOSITORY">Repository</option><option value="TEST">Test</option><option value="DEPLOYMENT">Deployment</option><option value="RUNTIME">Runtime</option></select></label><label className="field field--wide">Change reference<input value={reference} onChange={(event) => setReference(event.target.value)} placeholder="catalog-change:... or commit:..." required /></label><div className="form-actions"><button className="button button--primary" type="submit" disabled={busy}>Assess impact</button></div></form></details>
    </section>
  );
}

function WorkflowSection({ summary, busy, run }: { summary: GovernanceSummary; busy: boolean; run: (action: () => Promise<unknown>) => Promise<void> }) {
  const unassignedImpact = summary.impact_assessments.find(
    (impact) => !summary.workflow_cases.some((item) => item.impact_assessment_id === impact.id),
  );

  return (
    <section className="content-section" aria-labelledby="workflow-title">
      <div className="section-heading"><div><p className="section-kicker">Governed Workflow</p><h2 id="workflow-title">Human accountable change cases</h2><p>Release cannot be reached by skipping analysis, update, review, and approval gates.</p></div></div>
      {unassignedImpact && <button className="button button--secondary" type="button" disabled={busy} onClick={() => void run(() => createWorkflowCase(unassignedImpact.project_id, { impact_assessment_id: unassignedImpact.id, owner: "Technical Writer" }))}>Create workflow case for latest unassigned impact</button>}
      {summary.workflow_cases.length === 0 ? <p className="empty-state">No workflow cases yet.</p> : <div className="table-wrap"><table><thead><tr><th>Owner</th><th>State</th><th>Impact</th><th>Next gate</th></tr></thead><tbody>{summary.workflow_cases.map((item) => { const target = nextState[item.state]; return <tr key={item.id}><td>{item.owner}</td><td>{item.state.replace("_", " ")}</td><td>{item.impact_assessment_id}</td><td>{target ? <button className="button button--secondary" type="button" disabled={busy} onClick={() => void run(() => transitionWorkflowCase(item.id, { target_state: target, comment: "Advanced through governed project workflow." }))}>Move to {target.replace("_", " ")}</button> : "Complete"}</td></tr>; })}</tbody></table></div>}
    </section>
  );
}
