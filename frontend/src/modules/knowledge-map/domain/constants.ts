import type { Role } from "./types";

export const ROLE_LABELS: Record<Role, string> = {
  "po-ba": "PO / BA",
  developer: "Developer",
  qa: "QA / TW",
  devops: "DevOps",
};

export const URGENCY_LABELS: Record<string, string> = {
  critical: "Kritis",
  important: "Penting",
  deferrable: "Bisa nanti",
};

export const GAP_STATUS_LABELS: Record<string, string> = {
  ready: "Siap",
  partial: "Hampir Siap",
  missing: "Belum Siap",
};
