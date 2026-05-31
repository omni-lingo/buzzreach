/**
 * Signup page for new user registration (ONBOARD-001).
 *
 * Fields: email, username, password with strength meter.
 * Submit → POST /api/v1/auth/signup.
 * On success → redirect to /verify-email.
 */

import React, { useState } from "react";

const API_BASE = "/api/v1";

interface SignupResponse {
  user_id: string;
  username: string;
  email: string;
  message: string;
}

interface ApiError {
  detail: {
    error_code: string;
    message: string;
  };
}

type PasswordStrength = "weak" | "fair" | "strong";

function getPasswordStrength(password: string): PasswordStrength {
  if (password.length < 8) return "weak";
  const hasUpper = /[A-Z]/.test(password);
  const hasNumber = /\d/.test(password);
  const hasSpecial = /[^A-Za-z0-9]/.test(password);
  const score = [hasUpper, hasNumber, hasSpecial].filter(Boolean).length;
  if (score >= 3 && password.length >= 12) return "strong";
  if (score >= 2) return "fair";
  return "weak";
}

function strengthColor(strength: PasswordStrength): string {
  if (strength === "strong") return "#22c55e";
  if (strength === "fair") return "#f59e0b";
  return "#ef4444";
}

function strengthWidth(strength: PasswordStrength): string {
  if (strength === "strong") return "100%";
  if (strength === "fair") return "66%";
  return "33%";
}

async function submitSignup(
  email: string,
  username: string,
  password: string
): Promise<SignupResponse> {
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, username, password }),
  });
  if (!res.ok) {
    const err: ApiError = await res.json();
    throw new Error(err.detail.message);
  }
  const data: SignupResponse = await res.json();
  return data;
}

const Signup: React.FC = () => {
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [tosAgreed, setTosAgreed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const strength = getPasswordStrength(password);
  const isValid =
    email.trim() !== "" &&
    username.trim().length >= 3 &&
    password.length >= 8 &&
    tosAgreed;

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    if (!isValid || submitting) return;
    setError(null);
    setSubmitting(true);

    submitSignup(email, username, password)
      .then(() => {
        window.location.href = "/verify-email";
      })
      .catch((err: Error) => {
        setError(err.message);
        setSubmitting(false);
      });
  };

  return (
    <div className="signup-page">
      <h1>Create your account</h1>

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

        <label htmlFor="username">Username</label>
        <input
          id="username"
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          minLength={3}
          maxLength={150}
          autoComplete="username"
        />

        <label htmlFor="password">Password</label>
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

        {password.length > 0 && (
          <div className="password-strength">
            <div
              className="strength-bar"
              style={{
                width: strengthWidth(strength),
                backgroundColor: strengthColor(strength),
                height: "4px",
                borderRadius: "2px",
                transition: "width 0.2s",
              }}
            />
            <span className="strength-label">{strength}</span>
          </div>
        )}

        <label className="tos-checkbox">
          <input
            type="checkbox"
            checked={tosAgreed}
            onChange={(e) => setTosAgreed(e.target.checked)}
          />
          I agree to the Terms of Service
        </label>

        <button type="submit" disabled={!isValid || submitting}>
          {submitting ? "Creating account..." : "Sign up"}
        </button>
      </form>

      <p className="login-link">
        Already have an account? <a href="/login">Log in</a>
      </p>
    </div>
  );
};

export default Signup;
