/**
 * Account settings sub-components (FE-001).
 *
 * Split from AccountSettings.tsx by domain: password change form,
 * API key visibility toggle + copy + regenerate.
 */

import React, { useCallback, useState } from "react";

import { changePassword, regenerateApiKey } from "../api/settingsClient";

// --------------- Helpers ---------------

function getToken(): string {
  return localStorage.getItem("jwt_token") ?? "";
}

function validatePassword(password: string): string | null {
  if (password.length < 8) return "Password must be at least 8 characters";
  if (!/[A-Z]/.test(password)) return "Must contain an uppercase letter";
  if (!/\d/.test(password)) return "Must contain a number";
  return null;
}

// --------------- Password Change ---------------

export const PasswordSection: React.FC = () => {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const passwordError =
    newPassword.length > 0 ? validatePassword(newPassword) : null;
  const mismatch =
    confirmPassword.length > 0 && newPassword !== confirmPassword;

  const handleSubmit = useCallback(
    (e: React.FormEvent): void => {
      e.preventDefault();
      setError(null);
      setSuccess(null);

      if (!currentPassword) {
        setError("Current password is required");
        return;
      }
      if (passwordError) {
        setError(passwordError);
        return;
      }
      if (newPassword !== confirmPassword) {
        setError("Passwords do not match");
        return;
      }

      setSubmitting(true);
      changePassword(getToken(), {
        current_password: currentPassword,
        new_password: newPassword,
      })
        .then((res) => {
          setSuccess(res.message);
          setCurrentPassword("");
          setNewPassword("");
          setConfirmPassword("");
        })
        .catch((err: Error) => setError(err.message))
        .finally(() => setSubmitting(false));
    },
    [currentPassword, newPassword, confirmPassword, passwordError]
  );

  return (
    <fieldset className="settings-section">
      <legend>Change Password</legend>

      {error && <div className="field-error">{error}</div>}
      {success && <div className="success-banner">{success}</div>}

      <form onSubmit={handleSubmit}>
        <label htmlFor="currentPassword">Current password</label>
        <input
          id="currentPassword"
          type="password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          autoComplete="current-password"
        />

        <label htmlFor="newPassword">New password</label>
        <input
          id="newPassword"
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          minLength={8}
          maxLength={128}
          autoComplete="new-password"
        />
        {passwordError && (
          <span className="field-error">{passwordError}</span>
        )}

        <label htmlFor="confirmNewPassword">Confirm new password</label>
        <input
          id="confirmNewPassword"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          minLength={8}
          maxLength={128}
          autoComplete="new-password"
        />
        {mismatch && (
          <span className="field-error">Passwords do not match</span>
        )}

        <button
          type="submit"
          className="btn-change-password"
          disabled={submitting}
        >
          {submitting ? "Changing..." : "Change password"}
        </button>
      </form>
    </fieldset>
  );
};

// --------------- API Key Toggle & Copy ---------------

interface ApiKeyAccountProps {
  maskedKey: string;
  onRegenerated: () => void;
}

export const ApiKeyAccountSection: React.FC<ApiKeyAccountProps> = ({
  maskedKey,
  onRegenerated,
}) => {
  const [visible, setVisible] = useState(false);
  const [fullKey, setFullKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [keyError, setKeyError] = useState<string | null>(null);

  const displayKey = visible && fullKey ? fullKey : maskedKey;

  const handleToggle = useCallback((): void => {
    setVisible((prev) => !prev);
  }, []);

  const handleCopy = useCallback((): void => {
    const keyToCopy = fullKey ?? maskedKey;
    navigator.clipboard.writeText(keyToCopy).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [fullKey, maskedKey]);

  const handleRegenerate = useCallback((): void => {
    setRegenerating(true);
    setKeyError(null);
    regenerateApiKey(getToken())
      .then((res) => {
        setFullKey(res.api_key);
        setVisible(true);
        onRegenerated();
      })
      .catch((e: Error) => setKeyError(e.message))
      .finally(() => setRegenerating(false));
  }, [onRegenerated]);

  return (
    <fieldset className="settings-section">
      <legend>API Key</legend>
      <div className="api-key-row">
        <code className="api-key-value">{displayKey}</code>
        <button className="btn-toggle-key" onClick={handleToggle}>
          {visible ? "Hide" : "Show"}
        </button>
        <button className="btn-copy-key" onClick={handleCopy}>
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      {keyError && <span className="field-error">{keyError}</span>}
      <button
        className="btn-regenerate-key"
        onClick={handleRegenerate}
        disabled={regenerating}
      >
        {regenerating ? "Regenerating..." : "Regenerate key"}
      </button>
    </fieldset>
  );
};
