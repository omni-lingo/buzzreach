/**
 * API client functions for bulk opportunity actions (FEAT-006).
 */

export interface BulkResult {
  processed: number;
  failed: number;
  action: string;
}

const API_BASE = "/api/v1";

async function bulkRequest(
  path: string,
  ids: string[],
  method: string = "POST"
): Promise<Response> {
  return fetch(`${API_BASE}/opportunities/bulk${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ opportunity_ids: ids }),
  });
}

export async function bulkArchive(ids: string[]): Promise<BulkResult> {
  const res = await bulkRequest("/archive", ids);
  if (!res.ok) {
    const err: { detail: { message: string } } = await res.json();
    throw new Error(err.detail.message);
  }
  return res.json();
}

export async function bulkRegenerate(
  ids: string[]
): Promise<BulkResult> {
  const res = await bulkRequest("/regenerate", ids);
  if (!res.ok) {
    const err: { detail: { message: string } } = await res.json();
    throw new Error(err.detail.message);
  }
  return res.json();
}

export async function bulkExportCsv(ids: string[]): Promise<void> {
  const res = await bulkRequest("/export", ids);
  if (!res.ok) {
    const err: { detail: { message: string } } = await res.json();
    throw new Error(err.detail.message);
  }
  const blob = await res.blob();
  const disposition = res.headers.get("content-disposition") ?? "";
  const match = disposition.match(/filename="(.+)"/);
  const filename = match ? match[1] : "opportunities.csv";
  downloadBlob(blob, filename);
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function bulkDelete(ids: string[]): Promise<BulkResult> {
  const res = await bulkRequest("", ids, "DELETE");
  if (!res.ok) {
    const err: { detail: { message: string } } = await res.json();
    throw new Error(err.detail.message);
  }
  return res.json();
}
