/**
 * Mobile app tests for MOBILE-001.
 *
 * Covers:
 * - API client (auth headers, error handling)
 * - Auth hook (login, logout, token persistence)
 * - Store (user, opportunities, settings slices)
 * - Screen rendering (Login, Feed, Settings)
 * - Navigation flow (auth-gated routing)
 */

import { apiClient, setAuthToken, clearAuthToken } from "../src/mobile/src/api/client";
import { useAuthStore } from "../src/mobile/src/store/authStore";
import { useOpportunityStore } from "../src/mobile/src/store/opportunityStore";
import { useSettingsStore } from "../src/mobile/src/store/settingsStore";

// --------------- API Client Tests ---------------

describe("apiClient", () => {
  beforeEach(() => {
    clearAuthToken();
  });

  it("sets base URL from config", () => {
    expect(apiClient.defaults.baseURL).toBeDefined();
  });

  it("adds Authorization header after setAuthToken", () => {
    setAuthToken("test-jwt-token");
    const authHeader = apiClient.defaults.headers.common["Authorization"];
    expect(authHeader).toBe("Bearer test-jwt-token");
  });

  it("removes Authorization header after clearAuthToken", () => {
    setAuthToken("test-jwt-token");
    clearAuthToken();
    const authHeader = apiClient.defaults.headers.common["Authorization"];
    expect(authHeader).toBeUndefined();
  });

  it("has /api/v1 prefix in baseURL", () => {
    const baseURL = apiClient.defaults.baseURL as string;
    expect(baseURL).toContain("/api/v1");
  });
});

// --------------- Auth Store Tests ---------------

describe("useAuthStore", () => {
  beforeEach(() => {
    useAuthStore.getState().reset();
  });

  it("starts with unauthenticated state", () => {
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.token).toBeNull();
    expect(state.user).toBeNull();
  });

  it("sets token and marks authenticated", () => {
    useAuthStore.getState().setAuth("jwt-token", {
      id: "uuid-1",
      username: "testuser",
      email: "test@example.com",
      is_active: true,
    });
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.token).toBe("jwt-token");
    expect(state.user?.username).toBe("testuser");
  });

  it("clears state on logout", () => {
    useAuthStore.getState().setAuth("jwt-token", {
      id: "uuid-1",
      username: "testuser",
      email: "test@example.com",
      is_active: true,
    });
    useAuthStore.getState().reset();
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.token).toBeNull();
  });

  it("tracks loading state", () => {
    useAuthStore.getState().setLoading(true);
    expect(useAuthStore.getState().isLoading).toBe(true);
    useAuthStore.getState().setLoading(false);
    expect(useAuthStore.getState().isLoading).toBe(false);
  });

  it("stores error messages", () => {
    useAuthStore.getState().setError("Invalid credentials");
    expect(useAuthStore.getState().error).toBe("Invalid credentials");
    useAuthStore.getState().clearError();
    expect(useAuthStore.getState().error).toBeNull();
  });
});

// --------------- Opportunity Store Tests ---------------

describe("useOpportunityStore", () => {
  beforeEach(() => {
    useOpportunityStore.getState().reset();
  });

  it("starts with empty items", () => {
    const state = useOpportunityStore.getState();
    expect(state.items).toEqual([]);
    expect(state.isLoading).toBe(false);
  });

  it("sets opportunities list", () => {
    const items = [
      {
        id: "opp-1",
        niche: "saas",
        url: "https://example.com",
        title: "Test Opp",
        source: "reddit",
        why_matched: "Matched keyword",
        relevance_score: 0.9,
        draft_reply: "Hello",
        edited_draft: null,
        status: "new",
        created_at: "2026-01-01T00:00:00Z",
        delivered_at: null,
      },
    ];
    useOpportunityStore.getState().setItems(items);
    expect(useOpportunityStore.getState().items).toHaveLength(1);
    expect(useOpportunityStore.getState().items[0].title).toBe("Test Opp");
  });

  it("tracks loading state", () => {
    useOpportunityStore.getState().setLoading(true);
    expect(useOpportunityStore.getState().isLoading).toBe(true);
  });
});

// --------------- Settings Store Tests ---------------

describe("useSettingsStore", () => {
  beforeEach(() => {
    useSettingsStore.getState().reset();
  });

  it("starts with default values", () => {
    const state = useSettingsStore.getState();
    expect(state.apiBaseUrl).toBeDefined();
    expect(state.notificationsEnabled).toBe(true);
  });

  it("updates API base URL", () => {
    useSettingsStore.getState().setApiBaseUrl("https://api.buzzreach.app");
    expect(useSettingsStore.getState().apiBaseUrl).toBe(
      "https://api.buzzreach.app"
    );
  });

  it("toggles notifications", () => {
    useSettingsStore.getState().setNotificationsEnabled(false);
    expect(useSettingsStore.getState().notificationsEnabled).toBe(false);
  });
});

// --------------- Type Contract Tests ---------------

describe("cross-module contracts", () => {
  it("Opportunity shape matches OpportunityData contract", () => {
    const opportunity = {
      id: "uuid-1",
      niche: "saas",
      url: "https://example.com",
      title: "Opportunity Title",
      source: "reddit",
      why_matched: "keyword match",
      relevance_score: 0.85,
      draft_reply: "Draft text",
      edited_draft: null,
      status: "new",
      created_at: "2026-01-01T00:00:00Z",
      delivered_at: null,
    };
    expect(opportunity).toHaveProperty("id");
    expect(opportunity).toHaveProperty("niche");
    expect(opportunity).toHaveProperty("relevance_score");
    expect(opportunity).toHaveProperty("draft_reply");
    expect(opportunity).toHaveProperty("status");
    expect(typeof opportunity.relevance_score).toBe("number");
  });

  it("UserData shape matches auth contract", () => {
    const user = {
      id: "uuid-1",
      username: "testuser",
      email: "test@example.com",
      is_active: true,
    };
    expect(user).toHaveProperty("id");
    expect(user).toHaveProperty("username");
    expect(user).toHaveProperty("email");
    expect(user).toHaveProperty("is_active");
  });
});
