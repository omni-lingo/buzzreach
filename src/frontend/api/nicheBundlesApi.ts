/**
 * API client for niche bundles (QUALITY-004).
 *
 * Endpoints:
 *   GET  /api/v1/niche-bundles          — list bundles
 *   GET  /api/v1/niche-bundles/{id}     — get bundle
 *   POST /api/v1/niche-bundles/apply    — apply bundle
 */

const API_BASE = "/api/v1/niche-bundles";

// --------------- Types ---------------

export interface BundleTemplate {
  name: string;
  category: string;
  description: string;
  text: string;
}

export interface NicheBundle {
  id: string;
  name: string;
  slug: string;
  description: string;
  keywords: string[];
  platforms: string[];
  tone: string;
  tone_description: string;
  templates: BundleTemplate[];
  icon: string;
  created_at: string;
  updated_at: string;
}

interface BundleListResponse {
  items: NicheBundle[];
  total: number;
}

export interface ApplyBundleBody {
  bundle_id: string;
  profile_name: string;
  keywords?: string[];
  platforms?: string[];
}

export interface ApplyBundleResult {
  profile_id: string;
  profile_name: string;
  bundle_name: string;
  keywords: string[];
  platforms: string[];
  message: string;
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
    const body = await res.json().catch(() => ({}));
    const msg = body?.detail?.message || body?.message || res.statusText;
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

// --------------- API Functions ---------------

export async function fetchBundles(): Promise<NicheBundle[]> {
  const res = await fetch(API_BASE);
  const data = await handleResponse<BundleListResponse>(res);
  return data.items;
}

export async function fetchBundle(id: string): Promise<NicheBundle> {
  const res = await fetch(`${API_BASE}/${id}`);
  return handleResponse<NicheBundle>(res);
}

export async function applyBundle(
  token: string,
  body: ApplyBundleBody
): Promise<ApplyBundleResult> {
  const res = await fetch(`${API_BASE}/apply`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(body),
  });
  return handleResponse<ApplyBundleResult>(res);
}
