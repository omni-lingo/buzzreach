/**
 * Settings state store using Zustand (MOBILE-001).
 *
 * Manages user-configurable settings for the mobile app:
 * - API base URL (for self-hosted or staging)
 * - Notification preferences
 *
 * Cross-module contracts:
 * - Integrates with MOBILE-002 (push notifications)
 */

import { create } from "zustand";

const DEFAULT_API_URL = "http://localhost:8000";

interface SettingsState {
  apiBaseUrl: string;
  notificationsEnabled: boolean;
  setApiBaseUrl: (url: string) => void;
  setNotificationsEnabled: (enabled: boolean) => void;
  reset: () => void;
}

const initialState = {
  apiBaseUrl: DEFAULT_API_URL,
  notificationsEnabled: true,
};

/** Zustand store for app settings. */
const useSettingsStore = create<SettingsState>((set) => ({
  ...initialState,

  setApiBaseUrl: (apiBaseUrl: string) => set({ apiBaseUrl }),

  setNotificationsEnabled: (notificationsEnabled: boolean) =>
    set({ notificationsEnabled }),

  reset: () => set({ ...initialState }),
}));

export { useSettingsStore };
export type { SettingsState };
