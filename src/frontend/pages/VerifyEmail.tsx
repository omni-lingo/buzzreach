/**
 * Email verification landing page (ONBOARD-001).
 *
 * Shows after signup: "Check your email for verification link."
 * Provides a resend button, rate-limited to 3x per hour.
 */

import React, { useState } from "react";

const API_BASE = "/api/v1";

interface ResendResponse {
  message: string;
}

interface ApiError {
  detail: {
    error_code: string;
    message: string;
  };
}

async function resendVerification(email: string): Promise<ResendResponse> {
  const res = await fetch(`${API_BASE}/auth/resend-verification`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) {
    const err: ApiError = await res.json();
    throw new Error(err.detail.message);
  }
  const data: ResendResponse = await res.json();
  return data;
}

interface VerifyEmailProps {
  email?: string;
}

const VerifyEmail: React.FC<VerifyEmailProps> = ({ email = "" }) => {
  const [resendEmail, setResendEmail] = useState(email);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [resendCount, setResendCount] = useState(0);
  const [sending, setSending] = useState(false);

  const maxResends = 3;
  const canResend = resendCount < maxResends && !sending;

  const handleResend = (): void => {
    if (!canResend || !resendEmail.trim()) return;
    setError(null);
    setMessage(null);
    setSending(true);

    resendVerification(resendEmail)
      .then((res) => {
        setMessage(res.message);
        setResendCount((c) => c + 1);
        setSending(false);
      })
      .catch((err: Error) => {
        setError(err.message);
        setSending(false);
      });
  };

  return (
    <div className="verify-email-page">
      <h1>Verify your email</h1>
      <p>
        We sent a verification link to your email address. Please check your
        inbox and click the link to activate your account.
      </p>

      {message && <div className="success-banner">{message}</div>}
      {error && <div className="error-banner">{error}</div>}

      <div className="resend-section">
        <p>Didn&apos;t receive the email?</p>

        {!email && (
          <input
            type="email"
            placeholder="Enter your email"
            value={resendEmail}
            onChange={(e) => setResendEmail(e.target.value)}
          />
        )}

        <button onClick={handleResend} disabled={!canResend}>
          {sending ? "Sending..." : "Resend verification email"}
        </button>

        {resendCount > 0 && (
          <p className="resend-count">
            {resendCount} of {maxResends} resends used this session
          </p>
        )}
      </div>

      <p className="login-link">
        Already verified? <a href="/login">Log in</a>
      </p>
    </div>
  );
};

export default VerifyEmail;
