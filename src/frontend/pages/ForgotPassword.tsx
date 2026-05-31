/**
 * Forgot password page (ONBOARD-004).
 *
 * Email input → POST /api/v1/auth/forgot-password.
 * Shows a generic success message regardless of whether the email exists.
 */

import React, { useState } from "react";

const API_BASE = "/api/v1";

interface ApiError {
  detail: {
    error_code: string;
    message: string;
  };
}

async function submitForgotPassword(email: string): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) {
    const err: ApiError = await res.json();
    throw new Error(err.detail.message);
  }
}

const ForgotPassword: React.FC = () => {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const isValid = email.trim() !== "";

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    if (!isValid || submitting) return;
    setError(null);
    setSubmitting(true);

    submitForgotPassword(email)
      .then(() => {
        setSubmitted(true);
      })
      .catch((err: Error) => {
        setError(err.message);
        setSubmitting(false);
      });
  };

  if (submitted) {
    return (
      <div className="forgot-password-page">
        <h1>Check your email</h1>
        <p>
          If an account with that email exists, we sent a password reset link.
          The link expires in 6 hours.
        </p>
        <a href="/login" className="back-to-login">
          Back to login
        </a>
      </div>
    );
  }

  return (
    <div className="forgot-password-page">
      <h1>Forgot your password?</h1>
      <p>Enter your email and we'll send you a reset link.</p>

      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleSubmit}>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoComplete="email"
        />

        <button type="submit" disabled={!isValid || submitting}>
          {submitting ? "Sending..." : "Send reset link"}
        </button>
      </form>

      <p className="login-link">
        Remember your password? <a href="/login">Log in</a>
      </p>
    </div>
  );
};

export default ForgotPassword;
