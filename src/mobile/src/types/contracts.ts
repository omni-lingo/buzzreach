/**
 * TypeScript mirrors of cross-module contracts (MOBILE-001).
 *
 * These types mirror the Pydantic models in contracts/auth/user.py
 * and contracts/opportunity/opportunity.py. Changes to those contracts
 * must be reflected here.
 *
 * Cross-module contracts:
 * - UserData: consumed from AUTH-002 / API-001
 * - OpportunityData: consumed from PIPE-001 / API-001
 */

/** Mirrors contracts/auth/user.py — UserData. */
export interface UserData {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
}

/** Mirrors contracts/opportunity/opportunity.py — OpportunityData. */
export interface OpportunityData {
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

/** Login request body for username/password auth. */
export interface LoginRequest {
  username: string;
  password: string;
}

/** Login request body for API key auth. */
export interface ApiKeyLoginRequest {
  api_key: string;
}

/** Auth response from login endpoints. */
export interface AuthResponse {
  token: string;
  user: UserData;
}

/** Standard API error response. */
export interface ApiErrorResponse {
  error_code: string;
  message: string;
}

/** Opportunities list response. */
export interface OpportunitiesListResponse {
  items: OpportunityData[];
  total: number;
}

/**
 * Mirrors contracts/features/opportunity_action.py — ActionType.
 * Valid action types for opportunity tracking.
 */
export type ActionType = "viewed" | "copied" | "posted" | "archived";

/** Request body for logging an action on an opportunity. */
export interface LogActionRequest {
  action_type: ActionType;
  posted_url?: string;
}

/** Response from logging an action. */
export interface ActionResponse {
  id: string;
  opportunity_id: string;
  user_id: string;
  action_type: string;
  posted_url: string | null;
  created_at: string;
}
