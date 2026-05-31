/**
 * API client functions for the Filters page (FEAT-002).
 */

export interface FilterRule {
  id: string;
  user_id: string;
  name: string;
  rule_type: string;
  patterns: Record<string, unknown>;
  description: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface TestResult {
  rule_id: string;
  total: number;
  matched: number;
  rejected: number;
  sample_rejected: Array<{ url: string; title: string }>;
}

const API_BASE = "/api/v1";

export async function fetchRules(): Promise<FilterRule[]> {
  const res = await fetch(`${API_BASE}/filters`);
  if (!res.ok) throw new Error("Failed to fetch filter rules");
  const data: { rules: FilterRule[] } = await res.json();
  return data.rules;
}

export async function createRule(
  name: string,
  ruleType: string,
  patterns: Record<string, unknown>,
  description: string
): Promise<FilterRule> {
  const res = await fetch(`${API_BASE}/filters`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name,
      rule_type: ruleType,
      patterns,
      description,
    }),
  });
  if (!res.ok) {
    const err: { detail: { message: string } } = await res.json();
    throw new Error(err.detail.message);
  }
  return res.json();
}

export async function toggleRule(
  ruleId: string,
  enabled: boolean
): Promise<void> {
  const res = await fetch(`${API_BASE}/filters/${ruleId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  if (!res.ok) throw new Error("Failed to update rule");
}

export async function deleteRule(ruleId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/filters/${ruleId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete rule");
}

export async function testRule(ruleId: string): Promise<TestResult> {
  const res = await fetch(`${API_BASE}/filters/${ruleId}/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ limit: 100 }),
  });
  if (!res.ok) throw new Error("Failed to test rule");
  return res.json();
}

export function parsePatternInput(
  ruleType: string,
  raw: string
): Record<string, unknown> {
  if (ruleType === "regex") {
    return { regex: raw.split("\n").filter(Boolean) };
  }
  if (ruleType === "not") {
    return { keywords: raw.split("\n").filter(Boolean) };
  }
  if (ruleType === "field" || ruleType === "composite") {
    return JSON.parse(raw);
  }
  return {};
}
