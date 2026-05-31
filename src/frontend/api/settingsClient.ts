/**
 * API client for settings & account management (FE-001).
 *
 * Endpoints:
 *   GET  /api/v1/settings              — fetch user config
 *   POST /api/v1/settings              — save config changes
 *   POST /api/v1/settings/regenerate-key — regenerate API key
 *   POST /api/v1/password/change       — change password
 *
 * All calls include JWT auth via Authorization header.
 */

const API_BASE = "/api/v1";

// --------------- Types ---------------

export interface UsageStats {
  opportunities_found: number;
  drafts_generated: number;
}

export interface UserSettings {
  product_url: string;
  one_line_pitch: string;
  keywords: string[];
  tone: string;
  delivery_email: string;
  slack_webhook_url: string;
  delivery_frequency: "hourly" | "daily" | "weekly";
  platform_preferences: string[];
  exclude_domains: string[];
  api_key_masked: string;
  email: string;
  created_at: string;
  usage_stats: UsageStats;
}

export interface SaveSettingsRequest {
  product_url: string;
  one_line_pitch: string;
  keywords: string[];
  tone: string;
  delivery_email: string;
  slack_webhook_url: string;
  delivery_frequency: "hourly" | "daily" | "weekly";
  platform_preferences: string[];
  exclude_domains: string[];
}

export interface SaveSettingsResponse {
  message: string;
}

export interface RegenerateKeyResponse {
  api_key: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface ChangePasswordResponse {
  message: string;
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

// --------------- API Functions ---------------

export async function fetchSettings(
  token: string
): Promise<UserSettings> {
  const res = await fetch(`${API_BASE}/settings`, {
    headers: authHeaders(token),
  });
  return handleResponse<UserSettings>(res);
}

export async function saveSettings(
  token: string,
  settings: SaveSettingsRequest
): Promise<SaveSettingsResponse> {
  const res = await fetch(`${API_BASE}/settings`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(settings),
  });
  return handleResponse<SaveSettingsResponse>(res);
}

export async function regenerateApiKey(
  token: string
): Promise<RegenerateKeyResponse> {
  const res = await fetch(`${API_BASE}/settings/regenerate-key`, {
    method: "POST",
    headers: authHeaders(token),
  });
  return handleResponse<RegenerateKeyResponse>(res);
}

export async function changePassword(
  token: string,
  payload: ChangePasswordRequest
): Promise<ChangePasswordResponse> {
  const res = await fetch(`${API_BASE}/password/change`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
  return handleResponse<ChangePasswordResponse>(res);
}
