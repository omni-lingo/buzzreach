/**
 * Auth state store using Zustand (MOBILE-001).
 *
 * Manages:
 * - JWT token and user data
 * - Loading and error states for auth flows
 * - Authenticated flag derived from token presence
 *
 * Cross-module contracts:
 * - UserData shape from contracts/auth/user.py
 */

import { create } from "zustand";

import type { UserData } from "../types/contracts";

interface AuthState {
  token: string | null;
  user: UserData | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;
  error: string | null;
  setAuth: (token: string, user: UserData) => void;
  setLoading: (loading: boolean) => void;
  setInitialized: (initialized: boolean) => void;
  setError: (error: string) => void;
  clearError: () => void;
  reset: () => void;
}

const initialState = {
  token: null,
  user: null,
  isAuthenticated: false,
  isLoading: false,
  isInitialized: false,
  error: null,
};

/** Zustand store for authentication state. */
const useAuthStore = create<AuthState>((set) => ({
  ...initialState,

  setAuth: (token: string, user: UserData) =>
    set({ token, user, isAuthenticated: true, error: null }),

  setLoading: (isLoading: boolean) => set({ isLoading }),

  setInitialized: (isInitialized: boolean) => set({ isInitialized }),

  setError: (error: string) => set({ error, isLoading: false }),

  clearError: () => set({ error: null }),

  reset: () => set({ ...initialState }),
}));

export { useAuthStore };
export type { AuthState };
