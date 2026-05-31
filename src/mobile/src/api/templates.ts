/**
 * Template API client functions (QUALITY-003).
 *
 * Wraps axios calls for template CRUD operations.
 * All mutating requests go through the authenticated apiClient.
 *
 * Cross-module contracts:
 * - Calls QUALITY-003: /api/v1/templates
 * - Uses TemplateData from contracts/quality/draft_template.py
 */

import { apiClient } from "./client";
import type {
  TemplateCreateRequest,
  TemplateData,
  TemplateListResponse,
  TemplateUpdateRequest,
} from "../types/contracts";

interface TemplateFetchOptions {
  category?: string;
  search?: string;
  userId?: string;
}

/** Fetch templates with optional category/search filters. */
async function fetchTemplates(
  options?: TemplateFetchOptions
): Promise<TemplateData[]> {
  const params: Record<string, string> = {};
  if (options?.category) {
    params.category = options.category;
  }
  if (options?.search) {
    params.search = options.search;
  }
  if (options?.userId) {
    params.user_id = options.userId;
  }

  const response = await apiClient.get<TemplateListResponse>(
    "/templates",
    { params }
  );
  return response.data.items;
}

/** Create a new custom template. */
async function createTemplate(
  body: TemplateCreateRequest
): Promise<TemplateData> {
  const response = await apiClient.post<TemplateData>(
    "/templates",
    body
  );
  return response.data;
}

/** Update an existing template. */
async function updateTemplate(
  templateId: string,
  body: TemplateUpdateRequest
): Promise<TemplateData> {
  const response = await apiClient.put<TemplateData>(
    `/templates/${templateId}`,
    body
  );
  return response.data;
}

/** Delete a template. */
async function deleteTemplate(templateId: string): Promise<void> {
  await apiClient.delete(`/templates/${templateId}`);
}

export {
  fetchTemplates,
  createTemplate,
  updateTemplate,
  deleteTemplate,
};
export type { TemplateFetchOptions };
