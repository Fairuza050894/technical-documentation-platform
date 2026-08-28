import type { ProjectStage } from "../../app/router";
import type { ProjectReadiness } from "../../modules/workbench/governanceTypes";
import type { GeneratedDocumentSummary } from "../../modules/documents/types";
import type { Feature } from "../../modules/features/types";
import type { TechnicalSource } from "../../modules/sources/types";
import type { SynchronizationRun } from "../../modules/catalog/types";
import { Icon } from "../ui/Icon";

export interface StageDependencyData {
  features: Feature[];
  sources: TechnicalSource[];
  runs: SynchronizationRun[];
  documents: GeneratedDocumentSummary[];
  readiness: ProjectReadiness | null;
}

export interface StageDependencyIndicatorProps {
  stage: ProjectStage;
  data: StageDependencyData;
}

export interface StageStatus {
  state: "ready" | "warning" | "blocked" | "empty";
  message: string;
  count?: number;
}

export function resolveStageStatus(
  stage: ProjectStage,
  data: StageDependencyData,
): StageStatus {
  switch (stage) {
    case "overview":
      return { state: "ready", message: "Project overview" };

    case "features": {
      const active = data.features.filter(
        (feature) => feature.status === "ACTIVE",
      ).length;
      if (active === 0) {
        return {
          state: "warning",
          message: "No active features defined",
          count: 0,
        };
      }
      return {
        state: "ready",
        message: `${active} active features`,
        count: active,
      };
    }

    case "sources": {
      const ready = data.sources.filter(
        (source) => source.status === "READY",
      ).length;
      if (data.sources.length === 0) {
        return {
          state: "empty",
          message: "No sources imported",
          count: 0,
        };
      }
      if (ready === 0) {
        return {
          state: "warning",
          message: `${data.sources.length} sources, none ready`,
          count: data.sources.length,
        };
      }
      return {
        state: "ready",
        message: `${ready} ready sources`,
        count: ready,
      };
    }

    case "catalog": {
      const completed = data.runs.filter(
        (run) => run.status === "COMPLETED",
      ).length;
      const readySources = data.sources.filter(
        (source) => source.status === "READY",
      );
      if (readySources.length === 0) {
        return {
          state: "blocked",
          message: "Requires a ready source first",
          count: 0,
        };
      }
      if (completed === 0) {
        return {
          state: "warning",
          message: "No completed snapshots",
          count: 0,
        };
      }
      return {
        state: "ready",
        message: `${completed} snapshots`,
        count: completed,
      };
    }

    case "changes": {
      const completed = data.runs.filter(
        (run) => run.status === "COMPLETED",
      ).length;
      if (completed < 2) {
        return {
          state: "blocked",
          message: completed === 0
            ? "Requires 2 completed snapshots"
            : "Need 1 more snapshot for comparison",
          count: completed,
        };
      }
      return {
        state: "ready",
        message: `${completed} snapshots available`,
        count: completed,
      };
    }

    case "documents": {
      const approved = data.documents.filter(
        (document) => document.status === "APPROVED",
      ).length;
      const inReview = data.documents.filter(
        (document) =>
          document.status === "IN_REVIEW" ||
          document.status === "CHANGES_REQUESTED",
      ).length;
      if (data.readiness && data.readiness.required_not_ready_total > 0) {
        return {
          state: "warning",
          message: `${data.readiness.required_not_ready_total} required docs not ready`,
          count: data.documents.length,
        };
      }
      if (inReview > 0) {
        return {
          state: "warning",
          message: `${inReview} awaiting review`,
          count: data.documents.length,
        };
      }
      if (approved > 0) {
        return {
          state: "ready",
          message: `${approved} approved`,
          count: data.documents.length,
        };
      }
      return {
        state: data.documents.length > 0 ? "ready" : "empty",
        message:
          data.documents.length > 0
            ? `${data.documents.length} versions`
            : "No documents yet",
        count: data.documents.length,
      };
    }

    case "evidence": {
      const evidenceCount = data.readiness?.items.reduce(
        (sum, item) => sum + item.evidence_count,
        0,
      ) ?? 0;
      if (evidenceCount === 0) {
        return {
          state: "empty",
          message: "No evidence registered",
          count: 0,
        };
      }
      return {
        state: "ready",
        message: `${evidenceCount} evidence artifacts`,
        count: evidenceCount,
      };
    }

    default:
      return { state: "ready", message: "" };
  }
}

export function StageDependencyBadge({
  stage,
  data,
}: StageDependencyIndicatorProps) {
  const status = resolveStageStatus(stage, data);

  if (status.state === "ready" && stage === "overview") {
    return null;
  }

  return (
    <span
      className={`stage-dependency stage-dependency--${status.state}`}
      title={status.message}
      aria-label={status.message}
    >
      {status.state === "blocked" && <Icon name="alert" size={11} />}
      {status.state === "warning" && <Icon name="alert" size={11} />}
      {status.state === "empty" && <span className="stage-dependency__dot" />}
      {status.state === "ready" && status.count !== undefined && (
        <span className="stage-dependency__count">{status.count}</span>
      )}
    </span>
  );
}
