/**
 * Opportunity API client functions (MOBILE-003).
 *
 * Wraps axios calls for fetching opportunities and logging actions.
 * All requests go through the authenticated apiClient.
 *
 * Cross-module contracts:
 * - Calls API-001: GET /api/v1/opportunities
 * - Calls FEAT-003: POST /api/v1/opportunities/{id}/actions
 * - Uses OpportunityData from contracts/opportunity/opportunity.py
 * - Uses ActionType from contracts/features/opportunity_action.py
 */

import { apiClient } from "./client";
import type {
  ActionResponse,
  ActionType,
  LogActionRequest,
  OpportunityData,
} from "../types/contracts";

interface FetchOptions {
  niche?: string;
  status?: string;
}

/** Fetch opportunities with optional filters. Defaults to status=new. */
async function fetchOpportunities(
  options?: FetchOptions
): Promise<OpportunityData[]> {
  const params: Record<string, string> = { status: "new" };
  if (options?.niche) {
    params.niche = options.niche;
  }
  if (options?.status) {
    params.status = options.status;
  }

  const response = await apiClient.get<OpportunityData[]>(
    "/opportunities",
    { params }
  );
  return response.data;
}

/** Refresh opportunities with refresh=true flag for pull-to-refresh. */
async function refreshOpportunities(): Promise<OpportunityData[]> {
  const response = await apiClient.get<OpportunityData[]>(
    "/opportunities",
    { params: { refresh: "true", status: "new" } }
  );
  return response.data;
}

/** Log a user action (viewed, copied, posted, archived) on an opportunity. */
async function logOpportunityAction(
  opportunityId: string,
  actionType: ActionType,
  postedUrl?: string
): Promise<ActionResponse> {
  const body: LogActionRequest = { action_type: actionType };
  if (postedUrl) {
    body.posted_url = postedUrl;
  }

  const response = await apiClient.post<ActionResponse>(
    `/opportunities/${opportunityId}/actions`,
    body
  );
  return response.data;
}

export { fetchOpportunities, refreshOpportunities, logOpportunityAction };
export type { FetchOptions };
