/**
 * Webhooks management page (EXT-003).
 *
 * Displays the user's webhook configurations with controls to create,
 * test, toggle, delete webhooks, and view delivery history.
 */

import React, { useEffect, useState } from "react";

import {
  createWebhook,
  deleteWebhook,
  fetchDeliveryLogs,
  fetchWebhooks,
  testWebhook,
  updateWebhook,
} from "./webhooksApi";
import type { DeliveryLog, WebhookConfig } from "./webhooksApi";

const EVENT_TYPES = [
  "opportunity_created",
  "daily_digest",
] as const;

const WebhooksPage: React.FC = () => {
  const [webhooks, setWebhooks] = useState<WebhookConfig[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [newUrl, setNewUrl] = useState("");
  const [newEventType, setNewEventType] = useState<string>(
    EVENT_TYPES[0]
  );
  const [expandedLogs, setExpandedLogs] = useState<
    Record<string, DeliveryLog[]>
  >({});

  const loadWebhooks = (): void => {
    fetchWebhooks()
      .then(setWebhooks)
      .catch((e: Error) => setError(e.message));
  };

  useEffect(() => {
    loadWebhooks();
  }, []);

  const handleCreate = (): void => {
    setError(null);
    createWebhook(newUrl, newEventType)
      .then(() => {
        setNewUrl("");
        setShowForm(false);
        loadWebhooks();
      })
      .catch((e: Error) => setError(e.message));
  };

  const handleToggle = (
    id: string,
    currentActive: boolean
  ): void => {
    setError(null);
    updateWebhook(id, { active: !currentActive })
      .then(loadWebhooks)
      .catch((e: Error) => setError(e.message));
  };

  const handleDelete = (id: string): void => {
    setError(null);
    deleteWebhook(id)
      .then(loadWebhooks)
      .catch((e: Error) => setError(e.message));
  };

  const handleTest = (id: string): void => {
    setError(null);
    testWebhook(id)
      .then(() => setError(null))
      .catch((e: Error) => setError(e.message));
  };

  const handleViewLogs = (id: string): void => {
    if (expandedLogs[id]) {
      setExpandedLogs((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      return;
    }
    fetchDeliveryLogs(id)
      .then((logs) =>
        setExpandedLogs((prev) => ({ ...prev, [id]: logs }))
      )
      .catch((e: Error) => setError(e.message));
  };

  return (
    <div className="webhooks-page">
      <h1>Webhooks</h1>
      <p>
        Configure webhook endpoints to receive events in real time.
      </p>

      {error && <div className="error-banner">{error}</div>}

      <button
        onClick={() => setShowForm(!showForm)}
        className="new-webhook-btn"
      >
        {showForm ? "Cancel" : "New Webhook"}
      </button>

      {showForm && (
        <CreateForm
          url={newUrl}
          setUrl={setNewUrl}
          eventType={newEventType}
          setEventType={setNewEventType}
          onCreate={handleCreate}
        />
      )}

      <WebhookTable
        webhooks={webhooks}
        expandedLogs={expandedLogs}
        onToggle={handleToggle}
        onDelete={handleDelete}
        onTest={handleTest}
        onViewLogs={handleViewLogs}
      />

      {webhooks.length === 0 && (
        <p className="empty-state">
          No webhooks configured. Click &quot;New Webhook&quot; to
          add one.
        </p>
      )}
    </div>
  );
};

interface CreateFormProps {
  url: string;
  setUrl: (v: string) => void;
  eventType: string;
  setEventType: (v: string) => void;
  onCreate: () => void;
}

const CreateForm: React.FC<CreateFormProps> = ({
  url,
  setUrl,
  eventType,
  setEventType,
  onCreate,
}) => (
  <div className="new-webhook-form">
    <h2>Create Webhook</h2>
    <label>
      URL (HTTPS)
      <input
        type="url"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="https://example.com/webhook"
      />
    </label>
    <label>
      Event Type
      <select
        value={eventType}
        onChange={(e) => setEventType(e.target.value)}
      >
        {EVENT_TYPES.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>
    </label>
    <button onClick={onCreate} className="create-btn">
      Create Webhook
    </button>
  </div>
);

interface WebhookTableProps {
  webhooks: WebhookConfig[];
  expandedLogs: Record<string, DeliveryLog[]>;
  onToggle: (id: string, active: boolean) => void;
  onDelete: (id: string) => void;
  onTest: (id: string) => void;
  onViewLogs: (id: string) => void;
}

const WebhookTable: React.FC<WebhookTableProps> = ({
  webhooks,
  expandedLogs,
  onToggle,
  onDelete,
  onTest,
  onViewLogs,
}) => (
  <table className="webhooks-table">
    <thead>
      <tr>
        <th>URL</th>
        <th>Event</th>
        <th>Status</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {webhooks.map((wh) => (
        <React.Fragment key={wh.id}>
          <tr>
            <td title={wh.url}>{truncateUrl(wh.url)}</td>
            <td>{wh.event_type}</td>
            <td>
              <button
                onClick={() => onToggle(wh.id, wh.active)}
                className={wh.active ? "toggle-on" : "toggle-off"}
              >
                {wh.active ? "Active" : "Disabled"}
              </button>
              {wh.consecutive_failures > 0 && (
                <span className="failure-badge">
                  {wh.consecutive_failures} failures
                </span>
              )}
            </td>
            <td>
              <button onClick={() => onTest(wh.id)}>Test</button>
              <button onClick={() => onViewLogs(wh.id)}>
                Logs
              </button>
              <button
                onClick={() => onDelete(wh.id)}
                className="remove-btn"
              >
                Delete
              </button>
            </td>
          </tr>
          {expandedLogs[wh.id] && (
            <tr className="logs-row">
              <td colSpan={4}>
                <LogsTable logs={expandedLogs[wh.id]} />
              </td>
            </tr>
          )}
        </React.Fragment>
      ))}
    </tbody>
  </table>
);

interface LogsTableProps {
  logs: DeliveryLog[];
}

const LogsTable: React.FC<LogsTableProps> = ({ logs }) => (
  <div className="delivery-logs">
    <strong>Delivery History</strong>
    {logs.length === 0 && <p>No delivery attempts yet.</p>}
    <table className="logs-table">
      <thead>
        <tr>
          <th>Time</th>
          <th>Status</th>
          <th>Result</th>
        </tr>
      </thead>
      <tbody>
        {logs.map((entry) => (
          <tr key={entry.id}>
            <td>{new Date(entry.created_at).toLocaleString()}</td>
            <td>{entry.status_code ?? "N/A"}</td>
            <td className={entry.success ? "success" : "failure"}>
              {entry.success
                ? "OK"
                : entry.error_message || "Failed"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

function truncateUrl(url: string): string {
  return url.length > 50 ? url.slice(0, 47) + "..." : url;
}

export default WebhooksPage;
