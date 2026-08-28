export type TemplateCategory =
  | "REQUIREMENTS"
  | "ARCHITECTURE"
  | "TESTING"
  | "OPERATIONS"
  | "USER_FACING"
  | "GOVERNANCE";

export type TemplateStandard =
  | "IEEE 830"
  | "IEEE 829"
  | "ISO 9001:2015"
  | "ISO 27001:2022"
  | "ISO/IEC/IEEE 42010"
  | "ISO/IEC 26514"
  | "BABOK"
  | "OpenAPI 3.0"
  | "Custom";

export interface TemplateSummary {
  id: string;
  key: string;
  name: string;
  description: string;
  category: TemplateCategory;
  standard: string;
  document_type: string | null;
  is_builtin: boolean;
  version: number;
  section_count: number;
  created_at: string;
  updated_at: string;
}

export interface TemplateDetail extends TemplateSummary {
  content: string;
}

export interface TemplateCollection {
  items: TemplateSummary[];
  total: number;
}

export interface CreateTemplateInput {
  key: string;
  name: string;
  description: string;
  category: string;
  standard: string;
  content: string;
}

export interface UpdateTemplateInput {
  name?: string;
  description?: string;
  content?: string;
}

export const CATEGORY_LABELS: Record<TemplateCategory, string> = {
  REQUIREMENTS: "Requirements",
  ARCHITECTURE: "Architecture",
  TESTING: "Testing",
  OPERATIONS: "Operations",
  USER_FACING: "User-Facing",
  GOVERNANCE: "Governance",
};

export const CATEGORY_ORDER: TemplateCategory[] = [
  "REQUIREMENTS",
  "ARCHITECTURE",
  "TESTING",
  "OPERATIONS",
  "USER_FACING",
  "GOVERNANCE",
];
