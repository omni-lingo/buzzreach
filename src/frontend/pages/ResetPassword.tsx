/**
 * Reset password page (ONBOARD-004).
 *
 * Reads token from URL params (?token=...).
 * New password + confirm → POST /api/v1/auth/reset-password.
 * On success → redirect to /login.
 */

import React, { useState } from "react";

const API_BASE = "/api/v1";

interface ApiError {
  detail: {
    error_code: string;
    message: string;
  };
}

function getTokenFromUrl(): string {
  const params = new URLSearchParams(window.location.search);
  return params.get("token") ?? "";
}

async function submitResetPassword(
  token: string,
  newPassword: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  if (!res.ok) {
    const err: ApiError = await res.json();
    throw new Error(err.detail.message);
  }
}

function validatePassword(password: string): string | null {
  if (password.length < 8) return "Password must be at least 8 characters";
  if (!/[A-Z]/.test(password)) return "Must contain an uppercase letter";
  if (!/\d/.test(password)) return "Must contain a number";
  return null;
}

const ResetPassword: React.FC = () => {
  const [token] = useState(getTokenFromUrl);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const passwordError = password.length > 0 ? validatePassword(password) : null;
  const mismatch =
    confirmPassword.length > 0 && password !== confirmPassword;
  const isValid =
    token !== "" &&
    password.length >= 8 &&
    passwordError === null &&
    password === confirmPassword;

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    if (!isValid || submitting) return;
    setError(null);
    setSubmitting(true);

    submitResetPassword(token, password)
      .then(() => {
        setSuccess(true);
        setTimeout(() => {
          window.location.href = "/login";
        }, 2000);
      })
      .catch((err: Error) => {
        setError(err.message);
        setSubmitting(false);
      });
  };

  if (!token) {
    return (
      <div className="reset-password-page">
        <h1>Invalid reset link</h1>
        <p>This password reset link is invalid or has expired.</p>
        <a href="/forgot-password">Request a new reset link</a>
      </div>
    );
  }

  if (success) {
    return (
      <div className="reset-password-page">
        <h1>Password reset successful</h1>
        <p>Your password has been updated. Redirecting to login...</p>
        <a href="/login">Go to login</a>
      </div>
    );
  }

  return (
    <div className="reset-password-page">
      <h1>Set a new password</h1>

      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleSubmit}>
        <label htmlFor="password">New password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
          maxLength={128}
          autoComplete="new-password"
        />
        {passwordError && (
          <span className="field-error">{passwordError}</span>
        )}

        <label htmlFor="confirmPassword">Confirm password</label>
        <input
          id="confirmPassword"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
          minLength={8}
          maxLength={128}
          autoComplete="new-password"
        />
        {mismatch && (
          <span className="field-error">Passwords do not match</span>
        )}

        <button type="submit" disabled={!isValid || submitting}>
          {submitting ? "Resetting..." : "Reset password"}
        </button>
      </form>
    </div>
  );
};

export default ResetPassword;
