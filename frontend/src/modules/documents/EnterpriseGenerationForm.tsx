import { useEffect, useState } from "react";

import { getCurrentIdentity } from "../../shared/identity/api";
import type { CurrentIdentity } from "../../shared/identity/types";
import {
  generateEnterpriseDocument,
  getDocumentationChecklist,
  listDocumentTypes,
} from "./api";
import type {
  DocumentTypeDefinition,
  GeneratedDocumentDetail,
  ProjectDocumentationChecklist,
  ReadinessFinding,
} from "./types";

interface EnterpriseGenerationFormProps {
  projectId: string;
  onGenerated: (document: GeneratedDocumentDetail) => void;
}

export function EnterpriseGenerationForm({
  projectId,
  onGenerated,
}: EnterpriseGenerationFormProps) {
  const [documentTypes, setDocumentTypes] = useState<DocumentTypeDefinition[]>(
    [],
  );
  const [checklist, setChecklist] =
    useState<ProjectDocumentationChecklist | null>(null);
  const [selectedType, setSelectedType] = useState("");
  const [revisionReason, setRevisionReason] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [blockedFindings, setBlockedFindings] = useState<ReadinessFinding[]>(
    [],
  );
  const [identity, setIdentity] = useState<CurrentIdentity | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    void getCurrentIdentity(controller.signal)
      .then(setIdentity)
      .catch(() => setIdentity(null));
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!projectId) return;
    let isCurrent = true;
    void Promise.all([
      listDocumentTypes(),
      getDocumentationChecklist(projectId),
    ])
      .then(([registry, checklistData]) => {
        if (!isCurrent) return;
        setDocumentTypes(registry.items);
        setChecklist(checklistData);
        const firstType = registry.items[0];
        if (firstType && !selectedType) {
          setSelectedType(firstType.document_type);
        }
      })
      .catch(() => {
        if (isCurrent) {
          setMessage("Could not load document types.");
        }
      });
    return () => { isCurrent = false; };
  }, [projectId, selectedType]);

  async function handleGenerate(): Promise<void> {
    if (!projectId || !selectedType || isBusy) return;
    setIsBusy(true);
    setMessage(`Generating ${selectedType}...`);
    setBlockedFindings([]);
    try {
      const document = await generateEnterpriseDocument(
        projectId,
        selectedType,
        revisionReason,
      );
      setMessage(
        `Version ${document.version} generated as ${document.status}.`,
      );
      setRevisionReason("");
      onGenerated(document);
    } catch (error: unknown) {
      if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage("Enterprise document generation failed.");
      }
    } finally {
      setIsBusy(false);
    }
  }

  const selectedChecklistItem = checklist?.items.find(
    (item) => item.document_type === selectedType,
  );

  return (
    <div className="enterprise-generation-form">
      <div className="section-heading">
        <div>
          <h3>Enterprise document generation</h3>
          <p>
            Generate governed documents from evidence, claims, and source data.
            Readiness checks must pass before generation is allowed.
          </p>
        </div>
      </div>

      {checklist && (
        <div
          className="documentation-checklist"
          aria-label="Documentation checklist"
        >
          <div className="checklist-summary">
            <span>{checklist.total} types</span>
            <span>{checklist.available_total} available</span>
            <span>{checklist.missing_required_total} required missing</span>
          </div>
          <div className="checklist-items">
            {checklist.items.map((item) => (
              <div
                key={item.document_type}
                className={`checklist-item checklist-item--${item.availability.toLowerCase()}${
                  item.document_type === selectedType
                    ? " checklist-item--selected"
                    : ""
                }`}
                onClick={() => {
                  setSelectedType(item.document_type);
                  setBlockedFindings([]);
                }}
                role="button"
                tabIndex={0}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    setSelectedType(item.document_type);
                    setBlockedFindings([]);
                  }
                }}
              >
                <div className="checklist-item__header">
                  <strong>{item.display_name}</strong>
                  <span
                    className={`checklist-availability checklist-availability--${item.availability.toLowerCase()}`}
                  >
                    {item.availability}
                  </span>
                </div>
                <span className="checklist-item__meta">
                  {item.automation_profile} &middot; {item.requirement}
                </span>
                {item.latest_version && (
                  <span className="checklist-item__version">
                    Latest: v{item.latest_version} ({item.latest_status})
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="form-grid">
        <div className="field">
          <label htmlFor="enterprise-doc-type">Document type</label>
          <select
            id="enterprise-doc-type"
            value={selectedType}
            onChange={(event) => {
              setSelectedType(event.target.value);
              setBlockedFindings([]);
            }}
          >
            {documentTypes.map((type) => (
              <option key={type.document_type} value={type.document_type}>
                {type.display_name}
              </option>
            ))}
          </select>
        </div>

        <div className="field identity-summary" aria-live="polite">
          <span className="identity-summary__label">Generated by</span>
          {identity === null ? (
            <span className="identity-summary__loading">
              Resolving identity...
            </span>
          ) : (
            <>
              <strong>{identity.display_name}</strong>
              <small>{identity.provider}</small>
            </>
          )}
        </div>

        <div className="field field--wide">
          <label htmlFor="enterprise-revision-reason">Revision reason</label>
          <textarea
            id="enterprise-revision-reason"
            value={revisionReason}
            maxLength={500}
            placeholder="Describe why this version is being generated."
            onChange={(event) => setRevisionReason(event.target.value)}
          />
        </div>
      </div>

      {selectedChecklistItem && (
        <div className="readiness-status">
          <span
            className={`readiness-state readiness-state--${selectedChecklistItem.availability.toLowerCase()}`}
          >
            {selectedChecklistItem.availability}
          </span>
          <span>
            {selectedChecklistItem.automation_profile} &middot;{" "}
            {selectedChecklistItem.requirement}
          </span>
        </div>
      )}

      {blockedFindings.length > 0 && (
        <div className="blocked-findings" role="alert">
          <h4>Generation blocked</h4>
          <p>
            The following readiness checks must pass before this document can be
            generated:
          </p>
          <ul>
            {blockedFindings.map((finding) => (
              <li
                key={finding.rule_code}
                className={`finding finding--${finding.severity.toLowerCase()}`}
              >
                <strong>{finding.rule_code}</strong>
                <p>{finding.message}</p>
                {finding.missing_input && (
                  <p className="finding__missing">
                    Missing: {finding.missing_input}
                  </p>
                )}
                {finding.remediation && (
                  <p className="finding__remediation">
                    Remediation: {finding.remediation}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="form-actions">
        <button
          className="button button--primary"
          type="button"
          disabled={!selectedType || !projectId || isBusy}
          onClick={() => void handleGenerate()}
        >
          {isBusy
            ? "Generating..."
            : `Generate ${selectedType || "document"}`}
        </button>
      </div>

      <p className="loading-state" role="status">
        {message}
      </p>
    </div>
  );
}
