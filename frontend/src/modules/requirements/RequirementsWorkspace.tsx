import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { ApiClientError } from "../../shared/api/client";
import { Icon } from "../../shared/ui/Icon";
import { listFeatures } from "../features/api";
import type { Feature } from "../features/types";
import type { Project } from "../projects/types";
import { createRequirement, getTraceabilityCoverage, listRequirements } from "./api";
import type {
  CreateRequirementInput,
  Requirement,
  RequirementType,
  TraceabilityCoverage,
} from "./types";

interface RequirementsWorkspaceProps {
  workspaceId: string;
  project: Project;
}

const initialForm: CreateRequirementInput = {
  key: "",
  requirement_type: "SYSTEM",
  title: "",
  statement: "",
  owner: "",
  feature_id: null,
  acceptance_criteria: [],
  change_reason: "Initial governed requirement.",
};

export function RequirementsWorkspace({ workspaceId, project }: RequirementsWorkspaceProps) {
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [features, setFeatures] = useState<Feature[]>([]);
  const [coverage, setCoverage] = useState<TraceabilityCoverage | null>(null);
  const [loadState, setLoadState] = useState<"loading" | "ready" | "error">("loading");
  const [loadError, setLoadError] = useState("");
  const [form, setForm] = useState<CreateRequirementInput>(initialForm);
  const [criterion, setCriterion] = useState("");
  const [filter, setFilter] = useState("");
  const [formError, setFormError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const activeFeatures = useMemo(
    () => features.filter((feature) => feature.status === "ACTIVE"),
    [features],
  );

  const load = useCallback(
    async (signal?: AbortSignal): Promise<void> => {
      setLoadState("loading");
      setLoadError("");
      try {
        const [collection, traceability, featureCollection] = await Promise.all([
          listRequirements(workspaceId, project.id, signal),
          getTraceabilityCoverage(workspaceId, project.id, signal),
          listFeatures(workspaceId, project.id, signal),
        ]);
        setRequirements(collection.items);
        setCoverage(traceability);
        setFeatures(featureCollection.items);
        setLoadState("ready");
      } catch (error: unknown) {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setLoadError(error instanceof Error ? error.message : "Requirements could not be loaded.");
        setLoadState("error");
      }
    },
    [project.id, workspaceId],
  );

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const visibleRequirements = useMemo(() => {
    const query = filter.trim().toLowerCase();
    if (!query) return requirements;
    return requirements.filter((item) =>
      [item.key, item.title, item.statement, item.owner, item.requirement_type]
        .join(" ")
        .toLowerCase()
        .includes(query),
    );
  }, [filter, requirements]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setFormError("");
    setIsSubmitting(true);
    const acceptanceCriteria = criterion.trim() ? [criterion.trim()] : [];
    try {
      const created = await createRequirement(workspaceId, project.id, {
        ...form,
        acceptance_criteria: acceptanceCriteria,
      });
      setRequirements((current) => [...current, created]);
      setForm(initialForm);
      setCriterion("");
      const nextCoverage = await getTraceabilityCoverage(workspaceId, project.id);
      setCoverage(nextCoverage);
    } catch (error: unknown) {
      setFormError(
        error instanceof ApiClientError ? error.message : "The requirement could not be created.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  const isReadOnly = project.status === "ARCHIVED";

  return (
    <div className="feature-workspace">
      <header className="feature-workspace__header">
        <div>
          <p className="eyebrow">Governed product intent</p>
          <h2>Requirements &amp; traceability</h2>
          <p>
            Maintain immutable requirement revisions and verified links to implementation,
            evidence, and documentation.
          </p>
        </div>
        <span className="policy-badge">Traceability policy v1</span>
      </header>

      {isReadOnly && (
        <div className="notice notice--warning" role="status">
          <Icon name="alert" size={17} />
          <span>Archived projects keep requirements and traceability read-only.</span>
        </div>
      )}

      {loadState === "error" && (
        <div className="notice notice--error" role="alert">
          <span>{loadError}</span>
          <button type="button" className="button button--secondary" onClick={() => void load()}>
            Retry
          </button>
        </div>
      )}

      <section className="feature-signal-strip" aria-label="Requirement traceability summary">
        <RequirementSignal
          label="Active requirements"
          value={coverage?.total_requirements ?? requirements.length}
          detail="Latest governed revisions"
        />
        <RequirementSignal
          label="Fully traced"
          value={coverage?.fully_traced ?? 0}
          detail="Feature + evidence + document"
        />
        <RequirementSignal
          label="Traceability"
          value={`${coverage?.coverage_percent ?? 0}%`}
          detail="Verified links only"
        />
      </section>

      <div className="feature-workspace__grid">
        <section className="content-section feature-registry" aria-labelledby="requirement-registry-title">
          <div className="section-heading section-heading--split">
            <div>
              <h3 id="requirement-registry-title">Requirement registry</h3>
              <p>Each edit creates an immutable revision; historical facts are never overwritten.</p>
            </div>
            <span className="record-count">{requirements.length} records</span>
          </div>

          {loadState === "loading" && (
            <p className="loading-state" role="status">Loading requirements…</p>
          )}
          {loadState === "ready" && requirements.length === 0 && (
            <div className="empty-state">
              <span aria-hidden="true"><Icon name="documents" size={22} /></span>
              <h4>No governed requirements yet</h4>
              <p>Create the first requirement before treating downstream evidence as complete.</p>
            </div>
          )}

          {requirements.length > 0 && (
            <>
              <div className="list-filter">
                <input
                  type="search"
                  placeholder="Filter requirements by key, title, owner…"
                  value={filter}
                  onChange={(event) => setFilter(event.target.value)}
                  aria-label="Filter requirements"
                />
                {filter && (
                  <span className="record-count">
                    {visibleRequirements.length} of {requirements.length}
                  </span>
                )}
              </div>
              <div className="table-frame">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Requirement</th>
                      <th scope="col">Type</th>
                      <th scope="col">Owner</th>
                      <th scope="col">Traceability</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visibleRequirements.map((requirement) => {
                      const verifiedTypes = new Set(
                        requirement.trace_links
                          .filter((link) => link.verified)
                          .map((link) => link.target_type),
                      );
                      return (
                        <tr key={requirement.requirement_id}>
                          <td>
                            <strong>{requirement.title}</strong>
                            <span className="table-secondary-text">
                              <code>{requirement.key}</code> · revision {requirement.revision} · {requirement.status.toLowerCase()}
                            </span>
                            <span className="table-secondary-text">{requirement.statement}</span>
                          </td>
                          <td>
                            <span className="feature-kind-badge">
                              {formatType(requirement.requirement_type)}
                            </span>
                          </td>
                          <td>{requirement.owner}</td>
                          <td>
                            <strong>{verifiedTypes.size} / 3</strong>
                            <span className="table-secondary-text">verified target groups</span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </section>

        <section className="content-section" aria-labelledby="create-requirement-title">
          <div className="section-heading">
            <div>
              <h3 id="create-requirement-title">Create governed requirement</h3>
              <p>
                Keep statements testable, map implementation ownership, and record why the
                requirement enters the baseline.
              </p>
            </div>
          </div>
          <form className="form-panel" onSubmit={(event) => void handleSubmit(event)}>
            <div className="form-grid">
              <div className="field">
                <label htmlFor="requirement-key">Key</label>
                <input
                  id="requirement-key"
                  value={form.key}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, key: event.target.value.toUpperCase() }))
                  }
                  placeholder="REQ-001"
                  required
                  disabled={isReadOnly}
                />
              </div>
              <div className="field">
                <label htmlFor="requirement-type">Type</label>
                <select
                  id="requirement-type"
                  value={form.requirement_type}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      requirement_type: event.target.value as RequirementType,
                    }))
                  }
                  disabled={isReadOnly}
                >
                  <option value="BUSINESS">Business</option>
                  <option value="SYSTEM">System</option>
                  <option value="NON_FUNCTIONAL">Non-functional</option>
                  <option value="ACCEPTANCE">Acceptance</option>
                </select>
              </div>
              <div className="field field--wide">
                <label htmlFor="requirement-title">Title</label>
                <input
                  id="requirement-title"
                  value={form.title}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, title: event.target.value }))
                  }
                  required
                  disabled={isReadOnly}
                />
              </div>
              <div className="field field--wide">
                <label htmlFor="requirement-statement">Statement</label>
                <textarea
                  id="requirement-statement"
                  value={form.statement}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, statement: event.target.value }))
                  }
                  required
                  disabled={isReadOnly}
                />
              </div>
              <div className="field">
                <label htmlFor="requirement-owner">Owner</label>
                <input
                  id="requirement-owner"
                  value={form.owner}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, owner: event.target.value }))
                  }
                  required
                  disabled={isReadOnly}
                />
              </div>
              <div className="field">
                <label htmlFor="requirement-feature">Feature / module</label>
                <select
                  id="requirement-feature"
                  value={form.feature_id ?? ""}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      feature_id: event.target.value || null,
                    }))
                  }
                  disabled={isReadOnly}
                >
                  <option value="">Not mapped yet</option>
                  {activeFeatures.map((feature) => (
                    <option key={feature.id} value={feature.id}>
                      {feature.key} — {feature.name}
                    </option>
                  ))}
                </select>
                <small>
                  Selecting a verified project feature creates the implementation trace
                  automatically.
                </small>
              </div>
              <div className="field field--wide">
                <label htmlFor="requirement-criterion">Acceptance criterion</label>
                <textarea
                  id="requirement-criterion"
                  value={criterion}
                  onChange={(event) => setCriterion(event.target.value)}
                  placeholder="Optional but recommended for testable requirements"
                  disabled={isReadOnly}
                />
              </div>
              <div className="field field--wide">
                <label htmlFor="requirement-reason">Change reason</label>
                <input
                  id="requirement-reason"
                  value={form.change_reason}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, change_reason: event.target.value }))
                  }
                  required
                  disabled={isReadOnly}
                />
              </div>
            </div>
            {formError && <p className="form-error" role="alert">{formError}</p>}
            <div className="form-actions">
              <button
                type="submit"
                className="button button--primary"
                disabled={isReadOnly || isSubmitting}
              >
                {isSubmitting ? "Creating…" : "Create requirement"}
              </button>
            </div>
          </form>
        </section>
      </div>
    </div>
  );
}

function RequirementSignal({
  label,
  value,
  detail,
}: {
  label: string;
  value: string | number;
  detail: string;
}) {
  return (
    <div className="feature-signal">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

function formatType(value: RequirementType): string {
  return value
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
