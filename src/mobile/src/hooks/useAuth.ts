/**
 * Auth hook for login, logout, and token restoration (MOBILE-001).
 *
 * Handles:
 * - Login via API key (POST /api/v1/auth/login-api-key)
 * - Login via username/password (POST /api/v1/auth/login)
 * - Token persistence with expo-secure-store (encrypted)
 * - Auto-restore token on app launch (splash screen)
 * - Logout: clears token from storage and API client
 *
 * Cross-module contracts:
 * - Uses UserData, AuthResponse from contracts
 * - Calls API-001 authenticated endpoints
 */

import * as SecureStore from "expo-secure-store";

import {
  apiClient,
  clearAuthToken,
  parseApiError,
  setAuthToken,
} from "../api/client";
import { useAuthStore } from "../store/authStore";
import type { AuthResponse } from "../types/contracts";

const TOKEN_KEY = "buzzreach_auth_token";
const USER_KEY = "buzzreach_user_data";

/** Login with username and password. */
async function loginWithCredentials(
  username: string,
  password: string
): Promise<void> {
  const store = useAuthStore.getState();
  store.setLoading(true);
  store.clearError();

  try {
    const response = await apiClient.post<AuthResponse>("/auth/login", {
      username,
      password,
    });
    const { token, user } = response.data;

    await persistAuth(token, user);
    setAuthToken(token);
    store.setAuth(token, user);
  } catch (error: unknown) {
    store.setError(parseApiError(error));
  } finally {
    store.setLoading(false);
  }
}

/** Login with an API key. */
async function loginWithApiKey(apiKey: string): Promise<void> {
  const store = useAuthStore.getState();
  store.setLoading(true);
  store.clearError();

  try {
    const response = await apiClient.post<AuthResponse>(
      "/auth/login-api-key",
      { api_key: apiKey }
    );
    const { token, user } = response.data;

    await persistAuth(token, user);
    setAuthToken(token);
    store.setAuth(token, user);
  } catch (error: unknown) {
    store.setError(parseApiError(error));
  } finally {
    store.setLoading(false);
  }
}

/** Logout: clear stored token and reset state. */
async function logout(): Promise<void> {
  const store = useAuthStore.getState();

  try {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(USER_KEY);
  } catch {
    // Best-effort clear — storage errors are non-fatal
  }

  clearAuthToken();
  store.reset();
}

/**
 * Restore auth state from secure storage on app launch.
 * Called during splash screen to determine initial route.
 */
async function restoreAuth(): Promise<void> {
  const store = useAuthStore.getState();
  store.setLoading(true);

  try {
    const token = await SecureStore.getItemAsync(TOKEN_KEY);
    const userJson = await SecureStore.getItemAsync(USER_KEY);

    if (token && userJson) {
      const user = JSON.parse(userJson);
      setAuthToken(token);
      store.setAuth(token, user);
    }
  } catch {
    // Corrupted storage — force re-login
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(USER_KEY);
  } finally {
    store.setLoading(false);
    store.setInitialized(true);
  }
}

/** Persist token and user data to encrypted secure storage. */
async function persistAuth(
  token: string,
  user: { id: string; username: string; email: string; is_active: boolean }
): Promise<void> {
  await SecureStore.setItemAsync(TOKEN_KEY, token);
  await SecureStore.setItemAsync(USER_KEY, JSON.stringify(user));
}

export {
  loginWithCredentials,
  loginWithApiKey,
  logout,
  restoreAuth,
};
