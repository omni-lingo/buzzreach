/**
 * API client wrapper with auth interceptors (MOBILE-001).
 *
 * Uses axios with:
 * - Base URL from Expo config (extra.apiBaseUrl)
 * - JWT Authorization header injection via setAuthToken()
 * - Response error interceptor for structured error handling
 *
 * Cross-module contracts:
 * - Calls API-001 authenticated endpoints (/api/v1/*)
 * - Auth token format: Bearer <JWT>
 */

import axios, { AxiosError, AxiosInstance } from "axios";
import Constants from "expo-constants";

import type { ApiErrorResponse } from "../types/contracts";

const API_BASE_URL =
  Constants.expoConfig?.extra?.apiBaseUrl ?? "http://localhost:8000";

/** Pre-configured axios instance for BuzzReach API calls. */
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Set the JWT auth token on all future requests.
 * Called after successful login.
 */
function setAuthToken(token: string): void {
  apiClient.defaults.headers.common["Authorization"] = `Bearer ${token}`;
}

/**
 * Remove the auth token from all future requests.
 * Called on logout.
 */
function clearAuthToken(): void {
  delete apiClient.defaults.headers.common["Authorization"];
}

/** Extract a user-friendly message from an API error. */
function parseApiError(error: unknown): string {
  if (!axios.isAxiosError(error)) {
    return "An unexpected error occurred";
  }
  const axiosErr = error as AxiosError<{ detail: ApiErrorResponse }>;
  const detail = axiosErr.response?.data?.detail;
  if (detail?.message) {
    return detail.message;
  }
  if (axiosErr.response?.status === 401) {
    return "Authentication failed";
  }
  if (axiosErr.response?.status === 429) {
    return "Too many requests. Please try again later";
  }
  return axiosErr.message || "Network error";
}

// Response interceptor: log structured errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail: ApiErrorResponse }>) => {
    const status = error.response?.status;
    const errorCode = error.response?.data?.detail?.error_code;
    if (status && errorCode) {
      // Structured error available for callers
    }
    return Promise.reject(error);
  }
);

export { apiClient, setAuthToken, clearAuthToken, parseApiError };
