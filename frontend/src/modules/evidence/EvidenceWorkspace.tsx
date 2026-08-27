import { useEffect, useMemo, useState } from "react";

import {
  createClaim,
  listProjectClaims,
  listProjectEvidence,
  materializeEvidence,
  registerReferencedEvidence,
} from "./api";
import type {
  Claim,
  ClaimClassification,
  CreateClaimInput,
  EvidenceArtifact,
  RegisterReferencedEvidenceInput,
} from "./types";

interface EvidenceWorkspaceProject {
  id: string;
  name: string;
  key: string;
  status: string;
  workspace_id?: string;
}

interface EvidenceWorkspaceProps {
  project?: EvidenceWorkspaceProject;
  embedded?: boolean;
}

export function EvidenceWorkspace({
  project,
  embedded = false,
}: EvidenceWorkspaceProps) {
  const [projectId, setProjectId] = useState<string>(project?.id ?? "");
  const [evidence, setEvidence] = useState<EvidenceArtifact[]>([]);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [activeTab, setActiveTab] = useState<"evidence" | "claims">("evidence");
  const [evidenceFilter, setEvidenceFilter] = useState("");
  const [claimFilter, setClaimFilter] = useState("");
  const [showRegisterForm, setShowRegisterForm] = useState(false);
  const [showClaimForm, setShowClaimForm] = useState(false);
  const [isBusy, setIsBusy] = useState(false);
  const [message, setMessage] = useState("Select a project to view evidence.");

  const [registerKind, setRegisterKind] = useState<
    "USER_JOURNEY" | "DEPLOYMENT_RUNTIME" | "UAT_RESULT"
  >("USER_JOURNEY");
  const [registerSourceRef, setRegisterSourceRef] = useState("");
  const [registerOriginId, setRegisterOriginId] = useState("");
  const [registerChecksum, setRegisterChecksum] = useState("");
  const [registerContentRef, setRegisterContentRef] = useState("");
  const [registerCapturedAt, setRegisterCapturedAt] = useState("");

  const [claimStatement, setClaimStatement] = useState("");
  const [claimClassification, setClaimClassification] =
    useState<ClaimClassification>("OBSERVED");
  const [claimEvidenceIds, setClaimEvidenceIds] = useState<string[]>([]);
  const [claimDerivationRef, setClaimDerivationRef] = useState("");
  const [claimDocTypes, setClaimDocTypes] = useState("");

  useEffect(() => {
    if (project?.id) {
      setProjectId(project.id);
    }
  }, [project]);

  useEffect(() => {
    let isCurrent = true;
    if (!projectId) {
      setEvidence([]);
      setClaims([]);
      return () => {
        isCurrent = false;
      };
    }

    async function load(): Promise<void> {
      setMessage("Loading evidence workspace...");
      const currentProjectId = projectId;
      try {
        const [evidenceResult, claimsResult] = await Promise.all([
          listProjectEvidence(currentProjectId),
          listProjectClaims(currentProjectId),
        ]);
        if (!isCurrent) return;
        setEvidence(evidenceResult.items);
        setClaims(claimsResult.items);
        setMessage(
          evidenceResult.total === 0 && claimsResult.total === 0
            ? "No evidence or claims registered yet."
            : `${evidenceResult.total} evidence artifacts - ${claimsResult.total} claims`,
        );
      } catch (error: unknown) {
        if (isCurrent) {
          setMessage(
            error instanceof Error
              ? error.message
              : "Evidence workspace could not load.",
          );
        }
      }
    }

    void load();
    return () => {
      isCurrent = false;
    };
  }, [projectId]);

  const filteredEvidence = useMemo(() => {
    if (!evidenceFilter.trim()) return evidence;
    const query = evidenceFilter.trim().toLowerCase();
    return evidence.filter(
      (item) =>
        item.kind.toLowerCase().includes(query) ||
        item.source_reference.toLowerCase().includes(query) ||
        item.origin_id.toLowerCase().includes(query) ||
        item.content_reference.toLowerCase().includes(query),
    );
  }, [evidence, evidenceFilter]);

  const filteredClaims = useMemo(() => {
    if (!claimFilter.trim()) return claims;
    const query = claimFilter.trim().toLowerCase();
    return claims.filter(
      (item) =>
        item.statement.toLowerCase().includes(query) ||
        item.classification.toLowerCase().includes(query) ||
        item.asserted_by.toLowerCase().includes(query),
    );
  }, [claims, claimFilter]);

  async function handleRegister(): Promise<void> {
    if (!projectId || isBusy) return;
    setIsBusy(true);
    setMessage("Registering referenced evidence...");
    try {
      const input: RegisterReferencedEvidenceInput = {
        kind: registerKind,
        source_reference: registerSourceRef,
        origin_id: registerOriginId,
        checksum: registerChecksum,
        content_reference: registerContentRef,
        captured_at: new Date(registerCapturedAt).toISOString(),
      };
      const artifact = await registerReferencedEvidence(projectId, input);
      setEvidence((prev) => [...prev, artifact]);
      setShowRegisterForm(false);
      resetRegisterForm();
      setMessage(
        `Evidence ${artifact.id.slice(0, 8)} registered as ${formatKind(artifact.kind)}.`,
      );
    } catch (error: unknown) {
      setMessage(
        error instanceof Error ? error.message : "Evidence registration failed.",
      );
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCreateClaim(): Promise<void> {
    if (!projectId || isBusy) return;
    setIsBusy(true);
    setMessage("Creating claim...");
    try {
      const input: CreateClaimInput = {
        statement: claimStatement,
        classification: claimClassification,
        evidence_ids: claimEvidenceIds,
        derivation_reference:
          claimClassification === "INFERRED" ? claimDerivationRef : undefined,
        relevant_document_types: claimDocTypes
          ? claimDocTypes
              .split(",")
              .map((s) => s.trim())
              .filter(Boolean)
          : undefined,
      };
      const claim = await createClaim(projectId, input);
      setClaims((prev) => [...prev, claim]);
      setShowClaimForm(false);
      resetClaimForm();
      setMessage(
        `Claim ${claim.id.slice(0, 8)} created as ${claim.classification}.`,
      );
    } catch (error: unknown) {
      setMessage(
        error instanceof Error ? error.message : "Claim creation failed.",
      );
    } finally {
      setIsBusy(false);
    }
  }

  async function handleMaterialize(artifactId: string): Promise<void> {
    if (!projectId || isBusy) return;
    setIsBusy(true);
    setMessage("Materializing evidence...");
    try {
      await materializeEvidence(projectId, artifactId, {});
      setMessage(
        `Evidence ${artifactId.slice(0, 8)} materialized successfully.`,
      );
    } catch (error: unknown) {
      setMessage(
        error instanceof Error ? error.message : "Materialization failed.",
      );
    } finally {
      setIsBusy(false);
    }
  }

  function resetRegisterForm(): void {
    setRegisterKind("USER_JOURNEY");
    setRegisterSourceRef("");
    setRegisterOriginId("");
    setRegisterChecksum("");
    setRegisterContentRef("");
    setRegisterCapturedAt("");
  }

  function resetClaimForm(): void {
    setClaimStatement("");
    setClaimClassification("OBSERVED");
    setClaimEvidenceIds([]);
    setClaimDerivationRef("");
    setClaimDocTypes("");
  }

  function toggleClaimEvidence(id: string): void {
    setClaimEvidenceIds((prev) =>
      prev.includes(id)
        ? prev.filter((item) => item !== id)
        : [...prev, id],
    );
  }

  return (
    <div className="evidence-workspace">
      {!embedded && (
        <header className="topbar">
          <div>
            <p className="eyebrow">Evidence and claims governance</p>
            <h1>Evidence</h1>
          </div>
          <span className="environment-badge">Provenance tracked</span>
        </header>
      )}

      <nav className="document-tab-nav" aria-label="Evidence workspace sections">
        {(["evidence", "claims"] as const).map((tab) => (
          <button
            key={tab}
            type="button"
            className={
              activeTab === tab
                ? "document-tab document-tab--active"
                : "document-tab"
            }
            onClick={() => setActiveTab(tab)}
            aria-current={activeTab === tab ? "page" : undefined}
          >
            {tab === "evidence" ? "Evidence Artifacts" : "Claims"}
          </button>
        ))}
      </nav>

      {activeTab === "evidence" && (
        <section
          className="content-section"
          aria-labelledby="evidence-list-title"
        >
          <div className="section-heading section-heading--split">
            <div>
              <h2 id="evidence-list-title">Evidence artifacts</h2>
              <p>
                Immutable evidence records with provenance tracking and checksum
                verification.
              </p>
            </div>
            <div className="evidence-heading-actions">
              <span className="record-count">
                {evidence.length} artifacts
              </span>
              <button
                className="button button--primary"
                type="button"
                onClick={() => setShowRegisterForm(!showRegisterForm)}
              >
                {showRegisterForm ? "Cancel" : "Register evidence"}
              </button>
            </div>
          </div>

          {showRegisterForm && (
            <div className="form-panel">
              <h3>Register referenced evidence</h3>
              <p>
                Register external evidence such as user journeys, deployment
                records, or UAT results.
              </p>
              <div className="form-grid">
                <div className="field">
                  <label htmlFor="register-kind">Evidence kind</label>
                  <select
                    id="register-kind"
                    value={registerKind}
                    onChange={(event) =>
                      setRegisterKind(
                        event.target.value as typeof registerKind,
                      )
                    }
                  >
                    <option value="USER_JOURNEY">User Journey</option>
                    <option value="DEPLOYMENT_RUNTIME">
                      Deployment Runtime
                    </option>
                    <option value="UAT_RESULT">UAT Result</option>
                  </select>
                </div>
                <div className="field">
                  <label htmlFor="register-origin">Origin ID</label>
                  <input
                    id="register-origin"
                    required
                    maxLength={200}
                    value={registerOriginId}
                    onChange={(event) =>
                      setRegisterOriginId(event.target.value)
                    }
                    placeholder="unique-origin-identifier"
                  />
                </div>
                <div className="field field--wide">
                  <label htmlFor="register-source-ref">
                    Source reference
                  </label>
                  <input
                    id="register-source-ref"
                    required
                    maxLength={500}
                    value={registerSourceRef}
                    onChange={(event) =>
                      setRegisterSourceRef(event.target.value)
                    }
                    placeholder="https://example.com/evidence/source"
                  />
                </div>
                <div className="field field--wide">
                  <label htmlFor="register-content-ref">
                    Content reference
                  </label>
                  <input
                    id="register-content-ref"
                    required
                    maxLength={500}
                    value={registerContentRef}
                    onChange={(event) =>
                      setRegisterContentRef(event.target.value)
                    }
                    placeholder="https://example.com/evidence/content"
                  />
                </div>
                <div className="field">
                  <label htmlFor="register-checksum">
                    SHA-256 checksum
                  </label>
                  <input
                    id="register-checksum"
                    required
                    minLength={64}
                    maxLength={64}
                    pattern="[A-Fa-f0-9]{64}"
                    value={registerChecksum}
                    onChange={(event) =>
                      setRegisterChecksum(event.target.value)
                    }
                    placeholder="abcdef1234567890..."
                  />
                </div>
                <div className="field">
                  <label htmlFor="register-captured">Captured at</label>
                  <input
                    id="register-captured"
                    type="datetime-local"
                    required
                    value={registerCapturedAt}
                    onChange={(event) =>
                      setRegisterCapturedAt(event.target.value)
                    }
                  />
                </div>
              </div>
              <div className="form-actions">
                <button
                  className="button button--primary"
                  type="button"
                  disabled={isBusy}
                  onClick={() => void handleRegister()}
                >
                  {isBusy ? "Registering..." : "Register evidence"}
                </button>
              </div>
            </div>
          )}

          {evidence.length > 0 && (
            <div className="list-filter">
              <input
                type="search"
                placeholder="Filter evidence by kind, source, or origin..."
                value={evidenceFilter}
                onChange={(event) => setEvidenceFilter(event.target.value)}
                aria-label="Filter evidence artifacts"
              />
              {evidenceFilter && (
                <span className="record-count">
                  {filteredEvidence.length} of {evidence.length}
                </span>
              )}
            </div>
          )}

          {evidence.length === 0 ? (
            <div className="empty-state">
              <h3>No evidence artifacts</h3>
              <p>
                Register evidence to track provenance and support document
                generation.
              </p>
            </div>
          ) : (
            <div className="table-frame">
              <table>
                <thead>
                  <tr>
                    <th>Kind</th>
                    <th>Source</th>
                    <th>Origin</th>
                    <th>Checksum</th>
                    <th>Captured</th>
                    <th className="table-action-column">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEvidence.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <span
                          className={`evidence-kind evidence-kind--${item.kind.toLowerCase()}`}
                        >
                          {formatKind(item.kind)}
                        </span>
                        <span className="table-secondary-text">
                          {formatMethod(item.collection_method)}
                        </span>
                      </td>
                      <td>
                        <span className="evidence-source-ref">
                          {truncate(item.source_reference, 40)}
                        </span>
                        <span className="table-secondary-text">
                          {item.source_system}
                        </span>
                      </td>
                      <td>
                        <code>{item.origin_id}</code>
                      </td>
                      <td>
                        <code className="document-checksum-text">
                          {item.checksum.slice(0, 12)}
                        </code>
                      </td>
                      <td>{formatDate(item.captured_at)}</td>
                      <td className="table-action-column">
                        <button
                          className="button button--secondary"
                          type="button"
                          disabled={isBusy}
                          onClick={() => void handleMaterialize(item.id)}
                        >
                          Materialize
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filteredEvidence.length === 0 && evidenceFilter && (
                <div className="empty-state empty-state--compact">
                  <h3>No matching evidence</h3>
                  <p>Try a different search term.</p>
                </div>
              )}
            </div>
          )}
        </section>
      )}

      {activeTab === "claims" && (
        <section
          className="content-section"
          aria-labelledby="claims-list-title"
        >
          <div className="section-heading section-heading--split">
            <div>
              <h2 id="claims-list-title">Claims</h2>
              <p>
                Evidence-backed assertions that support document generation
                readiness.
              </p>
            </div>
            <div className="evidence-heading-actions">
              <span className="record-count">{claims.length} claims</span>
              <button
                className="button button--primary"
                type="button"
                onClick={() => setShowClaimForm(!showClaimForm)}
              >
                {showClaimForm ? "Cancel" : "Create claim"}
              </button>
            </div>
          </div>

          {showClaimForm && (
            <div className="form-panel">
              <h3>Create claim</h3>
              <p>Assert a fact backed by evidence artifacts.</p>
              <div className="form-grid">
                <div className="field field--wide">
                  <label htmlFor="claim-statement">Statement</label>
                  <textarea
                    id="claim-statement"
                    required
                    minLength={3}
                    maxLength={2000}
                    value={claimStatement}
                    onChange={(event) =>
                      setClaimStatement(event.target.value)
                    }
                    placeholder="Describe the claim being made."
                  />
                </div>
                <div className="field">
                  <label htmlFor="claim-classification">Classification</label>
                  <select
                    id="claim-classification"
                    value={claimClassification}
                    onChange={(event) =>
                      setClaimClassification(
                        event.target.value as ClaimClassification,
                      )
                    }
                  >
                    <option value="OBSERVED">Observed</option>
                    <option value="INFERRED">Inferred</option>
                    <option value="UNVERIFIED">Unverified</option>
                  </select>
                </div>
                {claimClassification === "INFERRED" && (
                  <div className="field">
                    <label htmlFor="claim-derivation">
                      Derivation reference
                    </label>
                    <input
                      id="claim-derivation"
                      maxLength={500}
                      value={claimDerivationRef}
                      onChange={(event) =>
                        setClaimDerivationRef(event.target.value)
                      }
                      placeholder="Deterministic derivation reference"
                    />
                  </div>
                )}
                <div className="field">
                  <label htmlFor="claim-doc-types">
                    Relevant document types
                  </label>
                  <input
                    id="claim-doc-types"
                    maxLength={200}
                    value={claimDocTypes}
                    onChange={(event) =>
                      setClaimDocTypes(event.target.value)
                    }
                    placeholder="HLD, LLD, AS_BUILT (comma-separated)"
                  />
                </div>
                {evidence.length > 0 && (
                  <div className="field field--wide">
                    <label>Supporting evidence</label>
                    <div className="evidence-checkbox-list">
                      {evidence.map((item) => (
                        <label key={item.id} className="evidence-checkbox">
                          <input
                            type="checkbox"
                            checked={claimEvidenceIds.includes(item.id)}
                            onChange={() => toggleClaimEvidence(item.id)}
                          />
                          <span>
                            {formatKind(item.kind)} &mdash; {item.origin_id}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <div className="form-actions">
                <button
                  className="button button--primary"
                  type="button"
                  disabled={isBusy}
                  onClick={() => void handleCreateClaim()}
                >
                  {isBusy ? "Creating..." : "Create claim"}
                </button>
              </div>
            </div>
          )}

          {claims.length > 0 && (
            <div className="list-filter">
              <input
                type="search"
                placeholder="Filter claims by statement, classification, or author..."
                value={claimFilter}
                onChange={(event) => setClaimFilter(event.target.value)}
                aria-label="Filter claims"
              />
              {claimFilter && (
                <span className="record-count">
                  {filteredClaims.length} of {claims.length}
                </span>
              )}
            </div>
          )}

          {claims.length === 0 ? (
            <div className="empty-state">
              <h3>No claims</h3>
              <p>
                Create claims to assert facts supported by evidence artifacts.
              </p>
            </div>
          ) : (
            <div className="table-frame">
              <table>
                <thead>
                  <tr>
                    <th>Statement</th>
                    <th>Classification</th>
                    <th>Evidence</th>
                    <th>Document types</th>
                    <th>Asserted by</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredClaims.map((claim) => (
                    <tr key={claim.id}>
                      <td>
                        <strong className="claim-statement">
                          {truncate(claim.statement, 80)}
                        </strong>
                      </td>
                      <td>
                        <span
                          className={`claim-classification claim-classification--${claim.classification.toLowerCase()}`}
                        >
                          {claim.classification}
                        </span>
                      </td>
                      <td>
                        <span className="record-count">
                          {claim.evidence_ids.length}
                        </span>
                      </td>
                      <td>
                        {claim.relevant_document_types.length > 0
                          ? claim.relevant_document_types.join(", ")
                          : "\u2014"}
                      </td>
                      <td>{claim.asserted_by}</td>
                      <td>{formatDate(claim.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filteredClaims.length === 0 && claimFilter && (
                <div className="empty-state empty-state--compact">
                  <h3>No matching claims</h3>
                  <p>Try a different search term.</p>
                </div>
              )}
            </div>
          )}
        </section>
      )}

      <p className="loading-state" role="status">
        {message}
      </p>
    </div>
  );
}

function formatKind(kind: string): string {
  return kind
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatMethod(method: string): string {
  return formatKind(method);
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function truncate(value: string, max: number): string {
  return value.length > max ? `${value.slice(0, max)}...` : value;
}
