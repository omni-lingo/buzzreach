/**
 * API client functions for the Webhooks page (EXT-003).
 */

export interface WebhookConfig {
  id: string;
  user_id: string;
  url: string;
  event_type: string;
  secret: string;
  active: boolean;
  consecutive_failures: number;
  created_at: string;
  updated_at: string;
}

export interface DeliveryLog {
  id: string;
  webhook_id: string;
  status_code: number | null;
  response_body: string;
  success: boolean;
  error_message: string;
  created_at: string;
}

const API_BASE = "/api/v1";

export async function fetchWebhooks(): Promise<WebhookConfig[]> {
  const res = await fetch(`${API_BASE}/webhooks`);
  if (!res.ok) throw new Error("Failed to fetch webhooks");
  return res.json();
}

export async function createWebhook(
  url: string,
  eventType: string
): Promise<WebhookConfig> {
  const res = await fetch(`${API_BASE}/webhooks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, event_type: eventType }),
  });
  if (!res.ok) {
    const err: { detail: { message: string } } = await res.json();
    throw new Error(err.detail.message);
  }
  return res.json();
}

export async function updateWebhook(
  webhookId: string,
  updates: { url?: string; event_type?: string; active?: boolean }
): Promise<WebhookConfig> {
  const res = await fetch(`${API_BASE}/webhooks/${webhookId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error("Failed to update webhook");
  return res.json();
}

export async function deleteWebhook(
  webhookId: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/webhooks/${webhookId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete webhook");
}

export async function testWebhook(
  webhookId: string
): Promise<{ status: string }> {
  const res = await fetch(
    `${API_BASE}/webhooks/${webhookId}/test`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error("Failed to send test webhook");
  return res.json();
}

export async function fetchDeliveryLogs(
  webhookId: string
): Promise<DeliveryLog[]> {
  const res = await fetch(
    `${API_BASE}/webhooks/${webhookId}/logs`
  );
  if (!res.ok) throw new Error("Failed to fetch delivery logs");
  return res.json();
}
