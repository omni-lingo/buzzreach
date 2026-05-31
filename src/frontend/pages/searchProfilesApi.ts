/**
 * API client for search profile endpoints (FEAT-004).
 *
 * Provides typed fetch wrappers for the /api/v1/search-profiles routes.
 */

const API_BASE = "/api/v1/search-profiles";

export interface SearchProfile {
  id: string;
  user_id: string;
  name: string;
  keywords: string[];
  platforms: string[];
  languages: string[];
  schedule_times: string[];
  schedule_frequency: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

interface ProfileListResponse {
  profiles: SearchProfile[];
  count: number;
}

interface CreateProfileBody {
  name: string;
  keywords: string[];
  platforms: string[];
  languages: string[];
  enabled: boolean;
  copy_from?: string;
}

interface UpdateProfileBody {
  name?: string;
  keywords?: string[];
  platforms?: string[];
  languages?: string[];
  enabled?: boolean;
}

interface ScheduleBody {
  times: string[];
  frequency: string;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const msg = body?.detail?.message || body?.message || res.statusText;
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

export async function fetchProfiles(): Promise<SearchProfile[]> {
  const res = await fetch(API_BASE);
  const data = await handleResponse<ProfileListResponse>(res);
  return data.profiles;
}

export async function createProfile(
  body: CreateProfileBody
): Promise<SearchProfile> {
  const res = await fetch(API_BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse<SearchProfile>(res);
}

export async function updateProfile(
  id: string,
  body: UpdateProfileBody
): Promise<SearchProfile> {
  const res = await fetch(`${API_BASE}/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse<SearchProfile>(res);
}

export async function deleteProfile(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail?.message || res.statusText);
  }
}

export async function setSchedule(
  id: string,
  body: ScheduleBody
): Promise<{ profile_id: string; times: string[]; frequency: string }> {
  const res = await fetch(`${API_BASE}/${id}/schedule`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
}

export function parseKeywords(input: string): string[] {
  return input
    .split("\n")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}
