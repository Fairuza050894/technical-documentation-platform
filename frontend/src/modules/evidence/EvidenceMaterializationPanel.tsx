import { useMemo, useState } from "react";

import { materializeEvidence } from "./api";
import type { EvidenceArtifact, EvidenceKind } from "./types";

const MATERIALIZABLE_KINDS: ReadonlySet<EvidenceKind> = new Set([
  "USER_JOURNEY",
  "DEPLOYMENT_RUNTIME",
  "UAT_RESULT",
]);

interface EvidenceMaterializationPanelProps {
  projectId: string;
  artifact: EvidenceArtifact;
  onCancel: () => void;
  onMaterialized: (message: string) => void;
}

// This pure boundary helper is intentionally colocated with the panel so the UI and test share
// the same materialization contract without duplicating policy constants.
// eslint-disable-next-line react-refresh/only-export-components
export function isMaterializableEvidence(kind: EvidenceKind): boolean {
  return MATERIALIZABLE_KINDS.has(kind);
}

export function EvidenceMaterializationPanel({
  projectId,
  artifact,
  onCancel,
  onMaterialized,
}: EvidenceMaterializationPanelProps) {
  const initialManifest = useMemo(() => defaultManifest(artifact.kind), [artifact.kind]);
  const [manifestText, setManifestText] = useState(() => JSON.stringify(initialManifest, null, 2));
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function submit(): Promise<void> {
    setError("");
    let manifest: Record<string, unknown>;
    try {
      const parsed: unknown = JSON.parse(manifestText);
      if (parsed === null || Array.isArray(parsed) || typeof parsed !== "object") {
        throw new Error("Manifest root must be a JSON object.");
      }
      manifest = parsed as Record<string, unknown>;
    } catch (parseError: unknown) {
      setError(parseError instanceof Error ? parseError.message : "Manifest must be valid JSON.");
      return;
    }

    setIsSubmitting(true);
    try {
      await materializeEvidence(projectId, artifact.id, manifest);
      onMaterialized(
        `Evidence ${artifact.id.slice(0, 8)} materialized and checksum-verified.`,
      );
    } catch (requestError: unknown) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Evidence materialization failed validation.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="form-panel" aria-labelledby="evidence-materialization-title">
      <div className="section-heading section-heading--split">
        <div>
          <p className="section-kicker">Governed semantic evidence</p>
          <h3 id="evidence-materialization-title">Materialize {formatKind(artifact.kind)}</h3>
          <p>
            Complete the typed manifest below. The backend canonicalizes it, rejects secret-like
            values, verifies its SHA-256 checksum against the registered artifact, and stores one
            immutable materialization.
          </p>
        </div>
        <code>{artifact.id.slice(0, 8)}</code>
      </div>
      <div className="field">
        <label htmlFor="evidence-manifest">Semantic evidence manifest</label>
        <textarea
          id="evidence-manifest"
          rows={18}
          value={manifestText}
          onChange={(event) => setManifestText(event.target.value)}
          spellCheck={false}
        />
        <small>
          Schema version is fixed to semantic-evidence-manifest-v1. Empty placeholder values must
          be replaced with source-backed facts before submission.
        </small>
      </div>
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="form-actions">
        <button
          className="button button--primary"
          type="button"
          disabled={isSubmitting}
          onClick={() => void submit()}
        >
          {isSubmitting ? "Validating…" : "Validate & materialize"}
        </button>
        <button
          className="button button--secondary"
          type="button"
          disabled={isSubmitting}
          onClick={onCancel}
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

function defaultManifest(kind: EvidenceKind): Record<string, unknown> {
  const common = {
    schema_version: "semantic-evidence-manifest-v1",
    kind,
  };
  switch (kind) {
    case "USER_JOURNEY":
      return {
        ...common,
        payload: {
          journey_name: "",
          actors: [],
          preconditions: [],
          steps: [],
          outcomes: [],
        },
      };
    case "DEPLOYMENT_RUNTIME":
      return {
        ...common,
        payload: {
          environment: "",
          runtime_components: [],
          prerequisites: [],
          configuration_keys: [],
          deployment_steps: [],
          verification_checks: [],
          rollback_references: [],
        },
      };
    case "UAT_RESULT":
      return {
        ...common,
        payload: {
          run_reference: "",
          executed_at: "",
          scenarios: [],
        },
      };
    case "SOURCE_ARTIFACT":
    case "CATALOG_SNAPSHOT":
      return common;
  }
}

function formatKind(kind: string): string {
  return kind
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
