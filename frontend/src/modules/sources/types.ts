export type SourceStatus = "READY" | "ARCHIVED";
export type SourceMediaType = "JSON" | "YAML";

export interface TechnicalSource {
  id: string;
  project_id: string;
  name: string;
  source_type: "OPENAPI_FILE";
  status: SourceStatus;
  original_file_name: string;
  media_type: SourceMediaType;
  checksum: string;
  openapi_version: string;
  api_title: string;
  api_version: string;
  path_count: number;
  operation_count: number;
  created_at: string;
  updated_at: string;
}

export interface SourceCollection {
  items: TechnicalSource[];
  total: number;
}
