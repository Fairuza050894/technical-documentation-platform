export type SynchronizationStatus = "RUNNING" | "COMPLETED" | "FAILED";

export interface SynchronizationRun {
  id: string;
  project_id: string;
  source_id: string;
  source_checksum: string;
  status: SynchronizationStatus;
  operation_count: number;
  schema_count: number;
  error_code: string;
  error_message: string;
  started_at: string;
  completed_at: string | null;
}

export interface ApiParameter {
  name: string;
  location: string;
  required: boolean;
  schema_type: string;
  schema_format: string;
  schema_reference: string;
}

export interface ApiPayload {
  required: boolean;
  media_types: string[];
  schema_types: string[];
  schema_references: string[];
}

export interface ApiResponseDefinition {
  status_code: string;
  description: string;
  media_types: string[];
  schema_types: string[];
  schema_references: string[];
}

export interface ApiOperation {
  synchronization_id: string;
  project_id: string;
  source_id: string;
  method: string;
  path: string;
  operation_id: string;
  summary: string;
  description: string;
  tags: string[];
  deprecated: boolean;
  security_schemes: string[];
  parameters: ApiParameter[];
  request_body: ApiPayload | null;
  responses: ApiResponseDefinition[];
  source_pointer: string;
}

export interface ApiSchemaProperty {
  name: string;
  schema_type: string;
  schema_format: string;
  required: boolean;
  reference: string;
  description: string;
}

export interface ApiSchema {
  synchronization_id: string;
  project_id: string;
  source_id: string;
  name: string;
  schema_type: string;
  description: string;
  required_fields: string[];
  properties: ApiSchemaProperty[];
  source_pointer: string;
}

export interface ApiCatalog {
  runs: SynchronizationRun[];
  operations: ApiOperation[];
  schemas: ApiSchema[];
  operation_total: number;
  schema_total: number;
}
