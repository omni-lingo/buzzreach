/**
 * API client for the Opportunities Dashboard (FE-002).
 *
 * Endpoints:
 *   GET  /api/v1/opportunities  — list with filters
 *   POST /api/v1/opportunities/{id}/mark-posted — record user action
 *   POST /api/v1/opportunities/{id}/archive     — hide from feed
 */

const API_BASE = "/api/v1";

// --------------- Types ---------------

export interface Opportunity {
  id: string;
  niche: string;
  url: string;
  title: string;
  source: string;
  why_matched: string;
  relevance_score: number;
  draft_reply: string;
  edited_draft: string | null;
  status: string;
  created_at: string;
  delivered_at: string | null;
}

export interface OpportunitiesResponse {
  items: Opportunity[];
  total: number;
}

export interface OpportunitiesFilters {
  platform?: string;
  score_min?: number;
  score_max?: number;
  status?: string;
  limit?: number;
  offset?: number;
}

export interface MarkPostedResponse {
  success: boolean;
}

export interface ArchiveResponse {
  success: boolean;
}

interface ApiError {
  detail: { error_code: string; message: string };
}

// --------------- Helpers ---------------

function authHeaders(token: string): Record<string, string> {
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err: ApiError = await res.json();
    throw new Error(err.detail.message);
  }
  return res.json();
}

function buildQueryString(filters: OpportunitiesFilters): string {
  const params = new URLSearchParams();
  if (filters.platform) {
    params.set("platform", filters.platform);
  }
  if (filters.score_min !== undefined) {
    params.set("score_min", String(filters.score_min));
  }
  if (filters.score_max !== undefined) {
    params.set("score_max", String(filters.score_max));
  }
  if (filters.status) {
    params.set("status", filters.status);
  }
  if (filters.limit !== undefined) {
    params.set("limit", String(filters.limit));
  }
  if (filters.offset !== undefined) {
    params.set("offset", String(filters.offset));
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

// --------------- API Functions ---------------

export async function fetchOpportunities(
  token: string,
  filters: OpportunitiesFilters = {}
): Promise<OpportunitiesResponse> {
  const qs = buildQueryString(filters);
  const res = await fetch(`${API_BASE}/opportunities${qs}`, {
    headers: authHeaders(token),
  });
  return handleResponse<OpportunitiesResponse>(res);
}

export async function markPosted(
  token: string,
  opportunityId: string
): Promise<MarkPostedResponse> {
  const res = await fetch(
    `${API_BASE}/opportunities/${opportunityId}/mark-posted`,
    {
      method: "POST",
      headers: authHeaders(token),
    }
  );
  return handleResponse<MarkPostedResponse>(res);
}

export async function archiveOpportunity(
  token: string,
  opportunityId: string
): Promise<ArchiveResponse> {
  const res = await fetch(
    `${API_BASE}/opportunities/${opportunityId}/archive`,
    {
      method: "POST",
      headers: authHeaders(token),
    }
  );
  return handleResponse<ArchiveResponse>(res);
}
