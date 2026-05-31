/**
 * Store barrel export (MOBILE-001).
 *
 * Re-exports all Zustand stores for convenient imports:
 * - authStore: JWT token, user data, auth state
 * - opportunityStore: opportunity feed items
 * - settingsStore: app configuration
 */

export { useAuthStore } from "./authStore";
export { useOpportunityStore } from "./opportunityStore";
export { useSettingsStore } from "./settingsStore";
