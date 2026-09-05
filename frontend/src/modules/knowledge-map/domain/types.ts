export type Role = "po-ba" | "developer" | "qa" | "devops";

export type GapStatus = "ready" | "partial" | "missing";

export interface DetectedFeature {
  key: string;
  name: string;
  source: "auto" | "manual";
  docStatus: GapStatus;
  docCount: number;
  docTotal: number;
  testStatus: GapStatus;
  testCount: number;
  testTotal: number;
}

export interface ActionItem {
  id: string;
  description: string;
  targetRole: Role;
  urgency: "critical" | "important" | "deferrable";
  relatedFeature?: string;
  remediation: string;
}

export interface OverviewStat {
  label: string;
  value: string;
  status: GapStatus;
  detail: string;
}

import type { ChangeItem } from "./changeTypes";

export interface KnowledgeMapData {
  overview: OverviewStat[];
  features: DetectedFeature[];
  actionItems: ActionItem[];
  recentChanges: ChangeItem[];
}
