/**
 * Settings & Configuration page (FE-001).
 *
 * Sections: product config, tone/persona, delivery preferences,
 * search filters, API key management, account info.
 * All API calls include JWT auth header.
 */

import React, { useCallback, useEffect, useState } from "react";

import type {
  SaveSettingsRequest,
  UserSettings,
} from "../api/settingsClient";
import {
  fetchSettings,
  regenerateApiKey,
  saveSettings,
} from "../api/settingsClient";
import type { SettingsFormData } from "../components/SettingsForm";
import SettingsForm from "../components/SettingsForm";

// --------------- Helpers ---------------

function getToken(): string {
  return localStorage.getItem("jwt_token") ?? "";
}

function toFormData(settings: UserSettings): SettingsFormData {
  return {
    product_url: settings.product_url,
    one_line_pitch: settings.one_line_pitch,
    keywords: settings.keywords.join("\n"),
    tone: settings.tone,
    delivery_email: settings.delivery_email,
    slack_webhook_url: settings.slack_webhook_url,
    delivery_frequency: settings.delivery_frequency,
    platform_preferences: settings.platform_preferences,
    exclude_domains: settings.exclude_domains.join("\n"),
  };
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

// --------------- Main Component ---------------

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  const loadSettings = useCallback((): void => {
    setLoading(true);
    setError(null);
    fetchSettings(getToken())
      .then(setSettings)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  const handleSave = useCallback(
    (data: SaveSettingsRequest): void => {
      setSaving(true);
      setError(null);
      setSuccess(null);
      saveSettings(getToken(), data)
        .then((res) => {
          setSuccess(res.message);
          loadSettings();
        })
        .catch((e: Error) => setError(e.message))
        .finally(() => setSaving(false));
    },
    [loadSettings]
  );

  if (loading) {
    return (
      <div className="settings-page">
        <p>Loading settings...</p>
      </div>
    );
  }

  if (error && !settings) {
    return (
      <div className="settings-page">
        <div className="error-banner">{error}</div>
        <button onClick={loadSettings}>Retry</button>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="settings-page">
        <p>No settings data available.</p>
      </div>
    );
  }

  return (
    <div className="settings-page">
      <h1>Settings</h1>

      {error && <div className="error-banner">{error}</div>}
      {success && <div className="success-banner">{success}</div>}

      <SettingsForm
        initial={toFormData(settings)}
        saving={saving}
        onSave={handleSave}
      />

      <ApiKeySection
        maskedKey={settings.api_key_masked}
        onRegenerated={loadSettings}
      />

      <AccountInfoSection
        email={settings.email}
        createdAt={settings.created_at}
        usageStats={settings.usage_stats}
      />
    </div>
  );
};

// --------------- API Key Section ---------------

interface ApiKeySectionProps {
  maskedKey: string;
  onRegenerated: () => void;
}

const ApiKeySection: React.FC<ApiKeySectionProps> = ({
  maskedKey,
  onRegenerated,
}) => {
  const [confirming, setConfirming] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [keyError, setKeyError] = useState<string | null>(null);

  const handleRegenerate = useCallback((): void => {
    setRegenerating(true);
    setKeyError(null);
    regenerateApiKey(getToken())
      .then((res) => {
        setNewKey(res.api_key);
        setConfirming(false);
        onRegenerated();
      })
      .catch((e: Error) => setKeyError(e.message))
      .finally(() => setRegenerating(false));
  }, [onRegenerated]);

  const displayKey = newKey ?? maskedKey;

  return (
    <fieldset className="settings-section api-key-section">
      <legend>API Key</legend>
      <div className="api-key-display">
        <code className="api-key-value">{displayKey}</code>
      </div>
      {keyError && <span className="field-error">{keyError}</span>}
      {newKey && (
        <p className="key-warning">
          Copy this key now. It will not be shown again.
        </p>
      )}
      {confirming ? (
        <div className="confirm-group">
          <p>This will invalidate your current API key.</p>
          <button
            className="btn-confirm-regenerate"
            onClick={handleRegenerate}
            disabled={regenerating}
          >
            {regenerating ? "Regenerating..." : "Confirm regenerate"}
          </button>
          <button
            className="btn-secondary"
            onClick={() => setConfirming(false)}
          >
            Cancel
          </button>
        </div>
      ) : (
        <button
          className="btn-regenerate-key"
          onClick={() => setConfirming(true)}
        >
          Regenerate API key
        </button>
      )}
    </fieldset>
  );
};

// --------------- Account Info Section ---------------

interface AccountInfoProps {
  email: string;
  createdAt: string;
  usageStats: { opportunities_found: number; drafts_generated: number };
}

const AccountInfoSection: React.FC<AccountInfoProps> = ({
  email,
  createdAt,
  usageStats,
}) => (
  <fieldset className="settings-section account-info-section">
    <legend>Account Info</legend>
    <table className="info-table">
      <tbody>
        <tr>
          <td>Email</td>
          <td>{email}</td>
        </tr>
        <tr>
          <td>Member since</td>
          <td>{formatDate(createdAt)}</td>
        </tr>
        <tr>
          <td>Opportunities found</td>
          <td>{usageStats.opportunities_found}</td>
        </tr>
        <tr>
          <td>Drafts generated</td>
          <td>{usageStats.drafts_generated}</td>
        </tr>
      </tbody>
    </table>
    <a href="/account" className="btn btn-secondary">
      Manage account
    </a>
  </fieldset>
);

export default Settings;
