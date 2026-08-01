import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { ApiClientError } from "../../shared/api/client";
import { Icon } from "../../shared/ui/Icon";
import type { Project } from "../projects/types";
import {
  archiveFeature,
  createFeature,
  getDocumentationMap,
  listFeatures,
} from "./api";
import type {
  CreateFeatureInput,
  DocumentationMap,
  DocumentationMapItem,
  Feature,
  FeatureKind,
} from "./types";

const initialForm: CreateFeatureInput = {
  key: "",
  name: "",
  description: "",
  kind: "FEATURE",
  owner: "",
};

interface FeatureWorkspaceProps {
  workspaceId: string;
  project: Project;
  selectedFeatureId: string | null;
  onOpenFeature: (featureId: string) => void;
  onCloseFeature: () => void;
}

export function FeatureWorkspace({
  workspaceId,
  project,
  selectedFeatureId,
  onOpenFeature,
  onCloseFeature,
}: FeatureWorkspaceProps) {
  const [features, setFeatures] = useState<Feature[]>([]);
  const [loadState, setLoadState] = useState<"loading" | "ready" | "error">("loading");
  const [loadError, setLoadError] = useState("");
  const [form, setForm] = useState<CreateFeatureInput>(initialForm);
  const [formError, setFormError] = useState("");
  const [actionError, setActionError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pendingArchiveId, setPendingArchiveId] = useState<string | null>(null);
  const [documentationMap, setDocumentationMap] = useState<DocumentationMap | null>(null);
  const [mapState, setMapState] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [mapError, setMapError] = useState("");

  const load = useCallback(
    async (signal?: AbortSignal): Promise<void> => {
      setLoadState("loading");
      setLoadError("");
      try {
        const response = await listFeatures(workspaceId, project.id, signal);
        setFeatures(response.items);
        setLoadState("ready");
      } catch (error: unknown) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setLoadError(
          error instanceof Error ? error.message : "Features and modules could not be loaded.",
        );
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

  const selectedFeature = useMemo(
    () => features.find((feature) => feature.id === selectedFeatureId) ?? null,
    [features, selectedFeatureId],
  );

  useEffect(() => {
    if (selectedFeatureId === null || selectedFeature === null) {
      setDocumentationMap(null);
      setMapState("idle");
      setMapError("");
      return;
    }

    const controller = new AbortController();
    setMapState("loading");
    setMapError("");
    void getDocumentationMap(
      workspaceId,
      project.id,
      selectedFeatureId,
      controller.signal,
    )
      .then((response) => {
        setDocumentationMap(response);
        setMapState("ready");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setMapError(
          error instanceof Error ? error.message : "The documentation map could not be loaded.",
        );
        setMapState("error");
      });
    return () => controller.abort();
  }, [project.id, selectedFeature, selectedFeatureId, workspaceId]);

  const activeFeatures = features.filter((feature) => feature.status === "ACTIVE");
  const modules = activeFeatures.filter((feature) => feature.kind === "MODULE");
  const missingRequired = activeFeatures.reduce(
    (total, feature) => total + feature.documentation_coverage.missing_required,
    0,
  );
  const isReadOnly = project.status === "ARCHIVED";

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setFormError("");
    setIsSubmitting(true);
    try {
      const created = await createFeature(workspaceId, project.id, form);
      setFeatures((current) => [...current, created]);
      setForm(initialForm);
      onOpenFeature(created.id);
    } catch (error: unknown) {
      setFormError(
        error instanceof ApiClientError ? error.message : "The feature could not be created.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleArchive(feature: Feature): Promise<void> {
    setActionError("");
    try {
      const archived = await archiveFeature(workspaceId, project.id, feature.id);
      setFeatures((current) =>
        current.map((item) => (item.id === archived.id ? archived : item)),
      );
      setPendingArchiveId(null);
    } catch (error: unknown) {
      setActionError(
        error instanceof ApiClientError ? error.message : "The feature could not be archived.",
      );
    }
  }

  return (
    <div className="feature-workspace">
      <header className="feature-workspace__header">
        <div>
          <p className="eyebrow">Project structure</p>
          <h2>Features &amp; modules</h2>
          <p>
            Define stable capability boundaries before requirements, evidence, and document
            versions are mapped.
          </p>
        </div>
        <span className="policy-badge">Baseline policy v1</span>
      </header>

      {isReadOnly && (
        <div className="notice notice--warning" role="status">
          <Icon name="alert" size={17} />
          <span>Archived projects keep their feature evidence read-only.</span>
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
      {actionError && <p className="form-error" role="alert">{actionError}</p>}

      <section className="feature-signal-strip" aria-label="Feature registry summary">
        <FeatureSignal label="Active capabilities" value={activeFeatures.length} detail={`${features.length} total`} />
        <FeatureSignal label="Modules" value={modules.length} detail={`${activeFeatures.length - modules.length} features`} />
        <FeatureSignal label="Required documents missing" value={missingRequired} detail="Calculated from baseline policy" />
      </section>

      <div className="feature-workspace__grid">
        <section className="content-section feature-registry" aria-labelledby="feature-registry-title">
          <div className="section-heading section-heading--split">
            <div>
              <h3 id="feature-registry-title">Capability registry</h3>
              <p>Keys are unique inside {project.name} and remain stable across future changes.</p>
            </div>
            <span className="record-count">{features.length} {features.length === 1 ? "item" : "items"}</span>
          </div>

          {loadState === "loading" && <p className="loading-state">Loading features and modules…</p>}
          {loadState === "ready" && features.length === 0 && (
            <div className="empty-state feature-empty-state">
              <span aria-hidden="true"><Icon name="projects" size={22} /></span>
              <h4>No features or modules yet</h4>
              <p>Create the first capability boundary to establish its documentation map.</p>
            </div>
          )}

          {features.length > 0 && (
            <div className="table-frame">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Capability</th>
                    <th scope="col">Type</th>
                    <th scope="col">Owner</th>
                    <th scope="col">Coverage</th>
                    <th scope="col" className="table-action-column">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {features.map((feature) => (
                    <tr key={feature.id} className={feature.id === selectedFeatureId ? "is-selected" : undefined}>
                      <td>
                        <strong>{feature.name}</strong>
                        <span className="table-secondary-text"><code>{feature.key}</code> · {feature.description || "No description"}</span>
                      </td>
                      <td><span className="feature-kind-badge">{formatFeatureKind(feature.kind)}</span></td>
                      <td>{feature.owner || "Unassigned"}</td>
                      <td>
                        <strong>{feature.documentation_coverage.available_required} / {feature.documentation_coverage.required_total}</strong>
                        <span className="table-secondary-text">required available</span>
                      </td>
                      <td className="table-action-column">
                        <span className="project-row-actions">
                          <button type="button" className="button button--secondary" onClick={() => onOpenFeature(feature.id)}>
                            Open map
                          </button>
                          {pendingArchiveId === feature.id ? (
                            <span className="inline-actions">
                              <button type="button" className="button button--danger-quiet" onClick={() => void handleArchive(feature)}>Confirm</button>
                              <button type="button" className="button button--quiet" onClick={() => setPendingArchiveId(null)}>Cancel</button>
                            </span>
                          ) : (
                            <button
                              type="button"
                              className="button button--quiet"
                              disabled={isReadOnly || feature.status === "ARCHIVED"}
                              onClick={() => setPendingArchiveId(feature.id)}
                            >
                              {feature.status === "ARCHIVED" ? "Archived" : "Archive"}
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

        <FeatureDocumentationMapPanel
          feature={selectedFeature}
          documentationMap={documentationMap}
          mapState={mapState}
          mapError={mapError}
          onClose={onCloseFeature}
        />
      </div>

      <section className="content-section" aria-labelledby="create-feature-title">
        <div className="section-heading">
          <div>
            <h3 id="create-feature-title">Create feature or module</h3>
            <p>The system applies a versioned documentation baseline according to the selected capability type.</p>
          </div>
        </div>
        <form className="form-panel" onSubmit={(event) => void handleSubmit(event)}>
          <div className="form-grid">
            <div className="field">
              <label htmlFor="feature-name">Name</label>
              <input id="feature-name" required minLength={3} maxLength={100} value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="Purchase Order" disabled={isReadOnly} />
            </div>
            <div className="field">
              <label htmlFor="feature-key">Feature key</label>
              <input id="feature-key" required minLength={2} maxLength={30} pattern="[A-Za-z][A-Za-z0-9-]+" value={form.key} onChange={(event) => setForm({ ...form, key: event.target.value.toUpperCase() })} placeholder="PURCHASE-ORDER" disabled={isReadOnly} />
            </div>
            <div className="field">
              <label htmlFor="feature-kind">Capability type</label>
              <select id="feature-kind" value={form.kind} onChange={(event) => setForm({ ...form, kind: event.target.value as FeatureKind })} disabled={isReadOnly}>
                <option value="FEATURE">Feature</option>
                <option value="MODULE">Module</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="feature-owner">Owner</label>
              <input id="feature-owner" maxLength={120} value={form.owner} onChange={(event) => setForm({ ...form, owner: event.target.value })} placeholder="ERP Product Team" disabled={isReadOnly} />
            </div>
            <div className="field field--wide">
              <label htmlFor="feature-description">Description</label>
              <textarea id="feature-description" rows={3} maxLength={1000} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="Describe the business capability and its boundary." disabled={isReadOnly} />
              <small>{form.description.length}/1000 characters</small>
            </div>
          </div>
          {formError && <p className="form-error" role="alert">{formError}</p>}
          <div className="form-actions">
            <button type="submit" className="button button--primary" disabled={isReadOnly || isSubmitting}>
              {isSubmitting ? "Creating…" : "Create capability"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

function FeatureSignal({ label, value, detail }: { label: string; value: number; detail: string }) {
  return (
    <div className="feature-signal">
      <small>{label}</small>
      <strong>{value}</strong>
      <span>{detail}</span>
    </div>
  );
}

function FeatureDocumentationMapPanel({
  feature,
  documentationMap,
  mapState,
  mapError,
  onClose,
}: {
  feature: Feature | null;
  documentationMap: DocumentationMap | null;
  mapState: "idle" | "loading" | "ready" | "error";
  mapError: string;
  onClose: () => void;
}) {
  return (
    <aside className="content-section feature-documentation-map" aria-labelledby="documentation-map-title">
      {feature === null ? (
        <div className="feature-map-placeholder">
          <span aria-hidden="true"><Icon name="documents" size={24} /></span>
          <h3 id="documentation-map-title">Documentation map</h3>
          <p>Select a feature or module to inspect its deterministic baseline coverage.</p>
        </div>
      ) : (
        <>
          <div className="section-heading section-heading--split">
            <div>
              <p className="section-kicker">{feature.key} · {formatFeatureKind(feature.kind)}</p>
              <h3 id="documentation-map-title">{feature.name}</h3>
              <p>{feature.documentation_coverage.missing_required} required documents need coverage.</p>
            </div>
            <button type="button" className="button button--quiet" onClick={onClose}>Close</button>
          </div>

          {mapState === "loading" && <p className="loading-state">Loading documentation map…</p>}
          {mapState === "error" && <p className="form-error" role="alert">{mapError}</p>}
          {mapState === "ready" && documentationMap !== null && (
            <>
              <div className="feature-policy-note">
                <Icon name="review" size={16} />
                <span>
                  <strong>Policy</strong>
                  <small>{documentationMap.policy_key}</small>
                </span>
              </div>
              <ul className="documentation-map-list">
                {documentationMap.items.map((item) => (
                  <DocumentationMapRow key={item.document_type} item={item} />
                ))}
              </ul>
              <p className="feature-map-footnote">
                Requirement and source evidence will refine this baseline through the deterministic impact engine in a later patch.
              </p>
            </>
          )}
        </>
      )}
    </aside>
  );
}

function DocumentationMapRow({ item }: { item: DocumentationMapItem }) {
  return (
    <li>
      <span className={`documentation-map-status documentation-map-status--${item.coverage_status.toLowerCase()}`} aria-hidden="true" />
      <span className="documentation-map-copy">
        <strong>{formatDocumentationType(item.document_type)}</strong>
        <small>{item.requirement === "REQUIRED" ? "Required by baseline" : "Optional baseline coverage"}</small>
      </span>
      <span className={`documentation-map-badge documentation-map-badge--${item.coverage_status.toLowerCase()}`}>
        {formatCoverageStatus(item.coverage_status)}
      </span>
    </li>
  );
}

function formatFeatureKind(kind: FeatureKind): string {
  return kind === "MODULE" ? "Module" : "Feature";
}

function formatDocumentationType(value: string): string {
  const labels: Record<string, string> = {
    BUSINESS_REQUIREMENT: "Business requirement",
    SYSTEM_REQUIREMENTS_SPECIFICATION: "System requirements specification",
    FUNCTIONAL_SPECIFICATION: "Functional specification",
    API_DOCUMENTATION: "API documentation",
    DATABASE_SPECIFICATION: "Database specification",
    USER_GUIDE: "User guide",
    TEST_SCENARIO: "Test scenario",
    RELEASE_NOTE: "Release note",
  };
  return labels[value] ?? value.replaceAll("_", " ").toLowerCase();
}

function formatCoverageStatus(value: DocumentationMapItem["coverage_status"]): string {
  switch (value) {
    case "AVAILABLE":
      return "Available";
    case "MISSING":
      return "Missing";
    case "PLANNED":
      return "Planned";
  }
}
