/**
 * API client for onboarding wizard (ONBOARD-003).
 *
 * Endpoints:
 *   GET  /api/v1/onboarding/status     — check if onboarding completed
 *   POST /api/v1/onboarding/save-step  — auto-save a wizard step
 *   POST /api/v1/onboarding/complete   — finalize onboarding, trigger scan
 *
 * All calls include JWT auth via Authorization header.
 */

const API_BASE = "/api/v1/onboarding";

// --------------- Types ---------------

export interface OnboardingStatus {
  onboarding_completed: boolean;
}

export interface SaveStepRequest {
  step: number;
  data: Record<string, unknown>;
}

export interface SaveStepResponse {
  message: string;
}

export interface CompleteRequest {
  product_url: string;
  one_line_pitch: string;
  keywords: string[];
  tone: string;
  plan_id: string;
}

export interface CompleteResponse {
  message: string;
  scan_queued: boolean;
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

export async function fetchOnboardingStatus(
  token: string
): Promise<OnboardingStatus> {
  const res = await fetch(`${API_BASE}/status`, {
    headers: authHeaders(token),
  });
  return handleResponse<OnboardingStatus>(res);
}

export async function saveOnboardingStep(
  token: string,
  payload: SaveStepRequest
): Promise<SaveStepResponse> {
  const res = await fetch(`${API_BASE}/save-step`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
  return handleResponse<SaveStepResponse>(res);
}

export async function completeOnboarding(
  token: string,
  payload: CompleteRequest
): Promise<CompleteResponse> {
  const res = await fetch(`${API_BASE}/complete`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
  return handleResponse<CompleteResponse>(res);
}
