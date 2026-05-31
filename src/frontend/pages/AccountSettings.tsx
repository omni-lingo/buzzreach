/**
 * Account Settings page (FE-001).
 *
 * Sections: email (read-only), password change, API key visibility
 * toggle + copy, delete account. All calls use JWT auth.
 * Heavy sub-components extracted to AccountSections.tsx.
 */

import React, { useCallback, useEffect, useState } from "react";

import type { UserSettings } from "../api/settingsClient";
import { fetchSettings } from "../api/settingsClient";
import {
  ApiKeyAccountSection,
  PasswordSection,
} from "../components/AccountSections";

// --------------- Helpers ---------------

function getToken(): string {
  return localStorage.getItem("jwt_token") ?? "";
}

// --------------- Main Component ---------------

const AccountSettings: React.FC = () => {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  if (loading) {
    return (
      <div className="account-settings-page">
        <p>Loading account info...</p>
      </div>
    );
  }

  if (error && !settings) {
    return (
      <div className="account-settings-page">
        <div className="error-banner">{error}</div>
        <button onClick={loadSettings}>Retry</button>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="account-settings-page">
        <p>No account data available.</p>
      </div>
    );
  }

  return (
    <div className="account-settings-page">
      <h1>Account Settings</h1>

      <EmailSection email={settings.email} />
      <PasswordSection />
      <ApiKeyAccountSection
        maskedKey={settings.api_key_masked}
        onRegenerated={loadSettings}
      />
      <DeleteAccountSection />
    </div>
  );
};

// --------------- Email (Read-Only) ---------------

const EmailSection: React.FC<{ email: string }> = ({ email }) => (
  <fieldset className="settings-section">
    <legend>Email Address</legend>
    <input
      id="accountEmail"
      type="email"
      value={email}
      disabled
      className="input-readonly"
    />
    <p className="help-text">Contact support to change your email.</p>
  </fieldset>
);

// --------------- Delete Account ---------------

const DeleteAccountSection: React.FC = () => {
  const [showConfirm, setShowConfirm] = useState(false);

  return (
    <fieldset className="settings-section danger-zone">
      <legend>Danger Zone</legend>
      {showConfirm ? (
        <div className="confirm-delete">
          <p>
            Are you sure? This action is permanent and cannot be undone.
          </p>
          <button className="btn-danger">Delete my account</button>
          <button
            className="btn-secondary"
            onClick={() => setShowConfirm(false)}
          >
            Cancel
          </button>
        </div>
      ) : (
        <button
          className="btn-danger-outline"
          onClick={() => setShowConfirm(true)}
        >
          Delete account
        </button>
      )}
    </fieldset>
  );
};

export default AccountSettings;
