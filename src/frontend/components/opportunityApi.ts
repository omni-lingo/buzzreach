/**
 * API client functions for opportunity actions (FEAT-003).
 */

export interface OpportunityAction {
  id: string;
  opportunity_id: string;
  user_id: string;
  action_type: string;
  posted_url: string | null;
  created_at: string;
}

export interface FunnelData {
  discovered: number;
  viewed: number;
  copied: number;
  posted: number;
  archived: number;
  conversion_rate: number;
}

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

export interface DraftResponse {
  original_draft: string;
  edited_draft: string | null;
  current_text: string;
}

export type DraftTone =
  | "professional"
  | "casual"
  | "humorous"
  | "technical"
  | "empathetic"
  | "enthusiastic";

const API_BASE = "/api/v1";

export async function logAction(
  opportunityId: string,
  actionType: string,
  postedUrl?: string
): Promise<OpportunityAction> {
  const body: Record<string, string> = { action_type: actionType };
  if (postedUrl) {
    body.posted_url = postedUrl;
  }
  const res = await fetch(
    `${API_BASE}/opportunities/${opportunityId}/actions`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }
  );
  if (!res.ok) {
    const err: { detail: { message: string } } = await res.json();
    throw new Error(err.detail.message);
  }
  return res.json();
}

export async function fetchActions(
  opportunityId: string
): Promise<OpportunityAction[]> {
  const res = await fetch(
    `${API_BASE}/opportunities/${opportunityId}/actions`
  );
  if (!res.ok) throw new Error("Failed to fetch actions");
  const data: { actions: OpportunityAction[] } = await res.json();
  return data.actions;
}

export async function fetchFunnel(params?: {
  platform?: string;
  dateFrom?: string;
  dateTo?: string;
}): Promise<FunnelData> {
  const query = new URLSearchParams();
  if (params?.platform) query.set("platform", params.platform);
  if (params?.dateFrom) query.set("date_from", params.dateFrom);
  if (params?.dateTo) query.set("date_to", params.dateTo);
  const qs = query.toString();
  const url = `${API_BASE}/analytics/funnel${qs ? `?${qs}` : ""}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch funnel data");
  return res.json();
}

export async function saveDraft(
  opportunityId: string,
  editedText: string
): Promise<DraftResponse> {
  const res = await fetch(
    `${API_BASE}/opportunities/${opportunityId}/draft`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ edited_text: editedText }),
    }
  );
  if (!res.ok) {
    const err: { detail: { message: string } } = await res.json();
    throw new Error(err.detail.message);
  }
  return res.json();
}

export async function discardDraft(
  opportunityId: string
): Promise<DraftResponse> {
  const res = await fetch(
    `${API_BASE}/opportunities/${opportunityId}/draft`,
    { method: "DELETE" }
  );
  if (!res.ok) throw new Error("Failed to discard draft");
  return res.json();
}

export async function regenerateDraft(
  opportunityId: string,
  tone: DraftTone
): Promise<DraftResponse> {
  const res = await fetch(
    `${API_BASE}/opportunities/${opportunityId}/regenerate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tone }),
    }
  );
  if (!res.ok) {
    const err: { detail: { message: string } } = await res.json();
    throw new Error(err.detail.message);
  }
  return res.json();
}

export async function deleteMyActions(): Promise<number> {
  const res = await fetch(`${API_BASE}/actions/me`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete actions");
  const data: { deleted_count: number } = await res.json();
  return data.deleted_count;
}
