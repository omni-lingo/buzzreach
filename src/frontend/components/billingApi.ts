/**
 * API client functions for billing portal (BILL-004).
 *
 * All calls require JWT auth via Authorization header.
 * No API keys are exposed in this file or in responses.
 */

const API_BASE = "/api/v1/billing";

export interface BillingOverview {
  plan_id: string;
  plan_name: string;
  price_cents: number;
  status: string;
  usage_current: number;
  usage_limit: number;
  usage_percentage: number;
  period_start: string | null;
  period_end: string | null;
  auto_renew: boolean;
  card_last4: string | null;
  card_brand: string | null;
  features: string[];
}

export interface Invoice {
  invoice_id: string;
  date: string;
  amount_cents: number;
  currency: string;
  status: string;
  pdf_url: string | null;
  description: string | null;
}

export interface InvoiceListResponse {
  invoices: Invoice[];
  total: number;
}

export interface PlanOption {
  plan_id: string;
  display_name: string;
  price_cents: number;
  opportunities_per_day: number;
  features: string[];
  is_current: boolean;
}

export interface PlanComparisonResponse {
  plans: PlanOption[];
}

export interface UpgradeResponse {
  checkout_url: string;
}

export interface DowngradeResponse {
  message: string;
  new_plan_id: string;
}

export interface CancelResponse {
  retention_offered: boolean;
  message: string;
}

export interface CancelConfirmResponse {
  message: string;
}

interface ApiError {
  detail: { error_code: string; message: string };
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err: ApiError = await res.json();
    throw new Error(err.detail.message);
  }
  return res.json();
}

export async function fetchBillingOverview(): Promise<BillingOverview> {
  const res = await fetch(`${API_BASE}/current`);
  return handleResponse<BillingOverview>(res);
}

export async function fetchInvoices(
  limit: number = 20
): Promise<InvoiceListResponse> {
  const res = await fetch(`${API_BASE}/invoices?limit=${limit}`);
  return handleResponse<InvoiceListResponse>(res);
}

export async function fetchPlans(): Promise<PlanComparisonResponse> {
  const res = await fetch(`${API_BASE}/plans`);
  return handleResponse<PlanComparisonResponse>(res);
}

export async function requestUpgrade(
  planId: string
): Promise<UpgradeResponse> {
  const res = await fetch(`${API_BASE}/upgrade`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ plan_id: planId }),
  });
  return handleResponse<UpgradeResponse>(res);
}

export async function requestDowngrade(
  planId: string
): Promise<DowngradeResponse> {
  const res = await fetch(`${API_BASE}/downgrade`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ plan_id: planId }),
  });
  return handleResponse<DowngradeResponse>(res);
}

export async function requestCancel(
  reason: string
): Promise<CancelResponse> {
  const res = await fetch(`${API_BASE}/cancel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  });
  return handleResponse<CancelResponse>(res);
}

export async function confirmCancel(): Promise<CancelConfirmResponse> {
  const res = await fetch(`${API_BASE}/cancel/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse<CancelConfirmResponse>(res);
}

export function formatPrice(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
