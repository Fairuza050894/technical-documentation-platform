import { requestJson } from "../../shared/api/client";
import type {
  CreateTemplateInput,
  TemplateCollection,
  TemplateDetail,
  UpdateTemplateInput,
} from "./types";

export function listTemplates(
  category?: string,
  documentType?: string,
  signal?: AbortSignal,
): Promise<TemplateCollection> {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  if (documentType) params.set("document_type", documentType);
  const query = params.toString();
  return requestJson<TemplateCollection>(`/templates${query ? `?${query}` : ""}`, { signal });
}

export function getTemplate(templateId: string): Promise<TemplateDetail> {
  return requestJson<TemplateDetail>(`/templates/${templateId}`);
}

export function getTemplateByKey(key: string): Promise<TemplateDetail> {
  return requestJson<TemplateDetail>(`/templates/by-key/${encodeURIComponent(key)}`);
}

export function createTemplate(input: CreateTemplateInput): Promise<TemplateDetail> {
  return requestJson<TemplateDetail>("/templates", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateTemplate(
  templateId: string,
  input: UpdateTemplateInput,
): Promise<TemplateDetail> {
  return requestJson<TemplateDetail>(`/templates/${templateId}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function deleteTemplate(templateId: string): Promise<void> {
  return requestJson<void>(`/templates/${templateId}`, { method: "DELETE" });
}

export function duplicateTemplate(
  templateId: string,
  key: string,
): Promise<TemplateDetail> {
  return requestJson<TemplateDetail>(`/templates/${templateId}/duplicate`, {
    method: "POST",
    body: JSON.stringify({ key }),
  });
}
