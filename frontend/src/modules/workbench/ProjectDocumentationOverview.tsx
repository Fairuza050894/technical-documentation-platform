import type { ProjectStage } from "../../app/router";
import { Icon } from "../../shared/ui/Icon";
import type { Project } from "../projects/types";
import type {
  ClaimClassification,
  DocumentReadiness,
  DocumentationChecklistItem,
  EvidenceArtifact,
  GovernedClaim,
  ProjectDocumentationContext,
  ReadinessFinding,
} from "./governanceTypes";

interface ProjectDocumentationOverviewProps {
  projectStatus: Project["status"];
  context: ProjectDocumentationContext | null;
  loadState: "loading" | "ready" | "error";
  error: string;
  onNavigateStage: (stage: ProjectStage) => void;
}

export function ProjectDocumentationOverview({
  projectStatus,
  context,
  loadState,
  error,
  onNavigateStage,
}: ProjectDocumentationOverviewProps) {
  if (loadState === "loading") {
    return (
      <section
        className="content-section project-documentation-overview"
        aria-labelledby="project-documentation-title"
      >
        <DocumentationHeading policyVersion="" />
        <p className="loading-state">Loading governed documentation status…</p>
      </section>
    );
  }

  if (loadState === "error" || context === null) {
    return (
      <section
        className="content-section project-documentation-overview"
        aria-labelledby="project-documentation-title"
      >
        <DocumentationHeading policyVersion="" />
        <div className="notice notice--error" role="alert">
          <span>{error || "Governed documentation status could not be loaded."}</span>
        </div>
      </section>
    );
  }

  const checklistByType = new Map(
    context.checklist.items.map((item) => [item.document_type, item]),
  );
  const evidenceById = new Map(context.evidence.map((item) => [item.id, item]));
  const requiredItems = context.readiness.items.filter((item) => item.requirement === "REQUIRED");
  const requiredAvailable = requiredItems.filter((item) => {
    const checklistItem = checklistByType.get(item.document_type);
    return (checklistItem?.availability ?? item.availability) === "AVAILABLE";
  }).length;

  return (
    <section
      className="content-section project-documentation-overview"
      aria-labelledby="project-documentation-title"
    >
      <DocumentationHeading policyVersion={context.readiness.policy_version} />

      {projectStatus === "ARCHIVED" && (
        <p className="documentation-read-only-note">
          Read-only view. Existing governance, readiness, evidence, and claims remain available.
        </p>
      )}

      <dl className="documentation-governance-summary">
        <DocumentationMetric
          label="Required coverage"
          value={`${requiredAvailable}/${requiredItems.length}`}
          detail="Required documents already created"
        />
        <DocumentationMetric
          label="Can proceed"
          value={String(context.readiness.eligible_total)}
          detail="Document workflows with no blockers"
        />
        <DocumentationMetric
          label="Blocked"
          value={String(context.readiness.not_ready_total)}
          detail="Documents with missing required inputs"
        />
      </dl>

      {context.readiness.items.length === 0 ? (
        <div className="documentation-governance-empty">
          <strong>No documentation readiness records are available.</strong>
          <span>The backend did not return a governed document checklist for this project.</span>
        </div>
      ) : (
        <ol className="documentation-readiness-list">
          {context.readiness.items.map((item) => (
            <DocumentationReadinessItem
              key={item.document_type}
              item={item}
              checklistItem={checklistByType.get(item.document_type) ?? null}
              evidenceById={evidenceById}
              claims={context.claims}
              onNavigateStage={onNavigateStage}
            />
          ))}
        </ol>
      )}
    </section>
  );
}

function DocumentationHeading({ policyVersion }: { policyVersion: string }) {
  return (
    <div className="section-heading section-heading--split">
      <div>
        <p className="section-kicker">Governed documentation</p>
        <h2 id="project-documentation-title">Project documentation</h2>
        <p>
          Availability shows whether a version exists. Readiness shows whether minimum governed
          inputs are sufficient to proceed.
        </p>
      </div>
      {policyVersion && <span className="record-count">Policy {policyVersion}</span>}
    </div>
  );
}

function DocumentationMetric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="documentation-governance-metric">
      <dt>{label}</dt>
      <dd>{value}</dd>
      <span>{detail}</span>
    </div>
  );
}

function DocumentationReadinessItem({
  item,
  checklistItem,
  evidenceById,
  claims,
  onNavigateStage,
}: {
  item: DocumentReadiness;
  checklistItem: DocumentationChecklistItem | null;
  evidenceById: Map<string, EvidenceArtifact>;
  claims: GovernedClaim[];
  onNavigateStage: (stage: ProjectStage) => void;
}) {
  const relevantClaims = claims.filter((claim) =>
    claim.relevant_document_types.includes(item.document_type),
  );
  const relatedEvidenceIds = new Set(relevantClaims.flatMap((claim) => claim.evidence_ids));
  const relatedEvidence = Array.from(relatedEvidenceIds)
    .map((evidenceId) => evidenceById.get(evidenceId))
    .filter((evidence): evidence is EvidenceArtifact => evidence !== undefined);
  const action = resolveDocumentAction(item, checklistItem);
  const availability = checklistItem?.availability ?? item.availability;
  const latestStatus = checklistItem?.latest_status ?? item.latest_status;

  return (
    <li className="documentation-readiness-item">
      <div className="documentation-readiness-item__identity">
        <div className="documentation-readiness-item__title">
          <strong>{item.display_name}</strong>
          <span className="documentation-requirement">
            {item.requirement === "REQUIRED" ? "Required" : "Supplementary"}
          </span>
        </div>
        <span>{formatAutomationProfile(item.automation_profile)}</span>
      </div>

      <div className="documentation-readiness-item__state">
        <span className={availabilityClass(availability)}>{formatAvailability(availability)}</span>
        <span className={readinessClass(item.readiness_state)}>
          {formatReadiness(item.readiness_state)}
        </span>
        {latestStatus !== null && (
          <span className={`status-badge status-badge--${latestStatus.toLowerCase()}`}>
            {formatLifecycle(latestStatus)}
          </span>
        )}
      </div>

      <div className="documentation-readiness-item__summary">
        <strong>{readinessSummary(item)}</strong>
        <span>
          {item.evidence_count} evidence records · {item.observed_claim_count} observed ·{" "}
          {item.inferred_claim_count} inferred · {item.unverified_claim_count} unverified
        </span>
      </div>

      <div className="documentation-readiness-item__actions">
        {action !== null && (
          <button
            type="button"
            className="button button--quiet"
            onClick={() => onNavigateStage(action.stage)}
          >
            {action.label}
            <Icon name="arrow-right" size={14} />
          </button>
        )}
      </div>

      <details className="documentation-readiness-details">
        <summary>Readiness details</summary>
        <div className="documentation-readiness-details__body">
          <FindingList findings={item.findings} />
          <TraceabilitySummary claims={relevantClaims} evidence={relatedEvidence} />
        </div>
      </details>
    </li>
  );
}

function FindingList({ findings }: { findings: ReadinessFinding[] }) {
  if (findings.length === 0) {
    return (
      <div className="documentation-readiness-clear">
        <Icon name="check" size={15} />
        <span>No blocker or warning remains for the current readiness policy.</span>
      </div>
    );
  }

  return (
    <div>
      <h3>Missing information</h3>
      <ul className="documentation-finding-list">
        {findings.map((finding) => (
          <li key={finding.rule_code}>
            <div className="documentation-finding-list__heading">
              <span className={findingClass(finding.severity)}>
                {formatFindingSeverity(finding.severity)}
              </span>
              <strong>{finding.message}</strong>
            </div>
            <p>{finding.remediation}</p>
            <small>Rule {finding.rule_code}</small>
          </li>
        ))}
      </ul>
    </div>
  );
}

function TraceabilitySummary({
  claims,
  evidence,
}: {
  claims: GovernedClaim[];
  evidence: EvidenceArtifact[];
}) {
  return (
    <div className="documentation-traceability">
      <h3>Traceability</h3>
      {claims.length === 0 ? (
        <p>No governed claims are mapped to this document type yet.</p>
      ) : (
        <ul>
          {claims.map((claim) => (
            <li key={claim.id}>
              <span className={claimClass(claim.classification)}>
                {formatClaimClassification(claim.classification)}
              </span>
              <span>{claim.statement}</span>
            </li>
          ))}
        </ul>
      )}
      <small>
        {evidence.length} directly referenced evidence artifact{evidence.length === 1 ? "" : "s"}
        {evidence.length > 0
          ? ` · ${evidence.map((item) => formatEvidenceKind(item.kind)).join(", ")}`
          : ""}
      </small>
    </div>
  );
}

function resolveDocumentAction(
  item: DocumentReadiness,
  checklistItem: DocumentationChecklistItem | null,
): { stage: ProjectStage; label: string } | null {
  if ((checklistItem?.availability ?? item.availability) === "AVAILABLE") {
    return { stage: "documents", label: "Open documents" };
  }

  for (const finding of item.findings) {
    if (finding.missing_input === "technical-evidence") {
      return { stage: "sources", label: "Add source evidence" };
    }
    if (finding.missing_input.includes("CATALOG_SNAPSHOT")) {
      return { stage: "catalog", label: "Create snapshot" };
    }
    if (finding.missing_input.startsWith("approved-documents")) {
      return { stage: "documents", label: "Review approvals" };
    }
  }

  return null;
}

function readinessSummary(item: DocumentReadiness): string {
  if (item.readiness_state === "READY") {
    return "Minimum governed inputs are available.";
  }
  if (item.readiness_state === "PARTIALLY_READY") {
    return `${item.findings.length} readiness warning${item.findings.length === 1 ? "" : "s"} remain.`;
  }
  const blockers = item.findings.filter((finding) => finding.severity === "BLOCKER").length;
  return `${blockers} blocking input${blockers === 1 ? "" : "s"} must be resolved.`;
}

function formatAutomationProfile(value: string): string {
  const labels: Record<string, string> = {
    EVIDENCE_DRIVEN: "Evidence-led",
    HYBRID: "Evidence + governed context",
    GOVERNED_AUTHORING: "Guided authoring",
    GOVERNED_BUNDLE: "Governed bundle",
  };
  return labels[value] ?? value.replaceAll("_", " ").toLowerCase();
}

function formatAvailability(value: string): string {
  return value === "AVAILABLE" ? "Available" : "Not created";
}

function availabilityClass(value: string): string {
  return value === "AVAILABLE"
    ? "result-label result-label--success"
    : "result-label result-label--neutral";
}

function formatReadiness(value: string): string {
  switch (value) {
    case "READY":
      return "Ready";
    case "PARTIALLY_READY":
      return "Ready with gaps";
    default:
      return "Blocked";
  }
}

function readinessClass(value: string): string {
  switch (value) {
    case "READY":
      return "result-label result-label--success";
    case "PARTIALLY_READY":
      return "result-label result-label--warning";
    default:
      return "result-label result-label--danger";
  }
}

function formatLifecycle(value: string): string {
  const labels: Record<string, string> = {
    DRAFT: "Draft",
    IN_REVIEW: "In review",
    CHANGES_REQUESTED: "Changes requested",
    APPROVED: "Approved",
    SUPERSEDED: "Previous version",
  };
  return labels[value] ?? value.replaceAll("_", " ").toLowerCase();
}

function formatFindingSeverity(value: string): string {
  if (value === "BLOCKER") {
    return "Blocking";
  }
  if (value === "WARNING") {
    return "Needs review";
  }
  return "Advisory";
}

function findingClass(value: string): string {
  if (value === "BLOCKER") {
    return "result-label result-label--danger";
  }
  if (value === "WARNING") {
    return "result-label result-label--warning";
  }
  return "result-label result-label--neutral";
}

function formatClaimClassification(value: ClaimClassification): string {
  switch (value) {
    case "OBSERVED":
      return "Observed";
    case "INFERRED":
      return "Inferred";
    case "UNVERIFIED":
      return "Unverified";
  }
}

function claimClass(value: ClaimClassification): string {
  if (value === "OBSERVED") {
    return "result-label result-label--success";
  }
  if (value === "INFERRED") {
    return "result-label result-label--warning";
  }
  return "result-label result-label--neutral";
}

function formatEvidenceKind(value: string): string {
  const labels: Record<string, string> = {
    SOURCE_ARTIFACT: "Source artifact",
    CATALOG_SNAPSHOT: "Catalog snapshot",
  };
  return labels[value] ?? value.replaceAll("_", " ").toLowerCase();
}
