export interface GeneratedDocumentSummary {
  id: string;
  project_id: string;
  source_id: string;
  target_run_id: string;
  baseline_run_id: string | null;
  document_type: "TECHNICAL_SOURCE_OVERVIEW";
  document_format: "MARKDOWN";
  title: string;
  file_name: string;
  checksum: string;
  operation_count: number;
  schema_count: number;
  breaking_change_count: number;
  generated_at: string;
}

export interface GeneratedDocumentDetail extends GeneratedDocumentSummary {
  content: string;
}

export interface GeneratedDocumentCollection {
  items: GeneratedDocumentSummary[];
  total: number;
}
