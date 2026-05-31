/**
 * Tests for opportunityStore (MOBILE-003).
 *
 * Validates state management for the opportunity feed.
 */

import { useOpportunityStore } from "../../store/opportunityStore";
import type { OpportunityData } from "../../types/contracts";

const MOCK_OPP: OpportunityData = {
  id: "opp-1",
  niche: "saas",
  url: "https://example.com/1",
  title: "Test opportunity",
  source: "reddit",
  why_matched: "Keyword match",
  relevance_score: 0.85,
  draft_reply: "Draft text",
  edited_draft: null,
  status: "new",
  created_at: "2024-01-01T00:00:00Z",
  delivered_at: null,
};

describe("opportunityStore", () => {
  beforeEach(() => {
    useOpportunityStore.getState().reset();
  });

  it("starts with empty items", () => {
    const state = useOpportunityStore.getState();
    expect(state.items).toEqual([]);
    expect(state.isLoading).toBe(false);
    expect(state.isRefreshing).toBe(false);
    expect(state.error).toBeNull();
    expect(state.selectedId).toBeNull();
  });

  it("setItems replaces items and clears loading", () => {
    const store = useOpportunityStore.getState();
    store.setLoading(true);
    store.setItems([MOCK_OPP]);

    const state = useOpportunityStore.getState();
    expect(state.items).toHaveLength(1);
    expect(state.items[0].id).toBe("opp-1");
    expect(state.isLoading).toBe(false);
  });

  it("appendItems adds to existing items", () => {
    const store = useOpportunityStore.getState();
    store.setItems([MOCK_OPP]);

    const second: OpportunityData = { ...MOCK_OPP, id: "opp-2" };
    store.appendItems([second]);

    expect(useOpportunityStore.getState().items).toHaveLength(2);
  });

  it("removeItem removes by id", () => {
    const store = useOpportunityStore.getState();
    store.setItems([MOCK_OPP, { ...MOCK_OPP, id: "opp-2" }]);

    store.removeItem("opp-1");

    const items = useOpportunityStore.getState().items;
    expect(items).toHaveLength(1);
    expect(items[0].id).toBe("opp-2");
  });

  it("setRefreshing toggles refreshing flag", () => {
    const store = useOpportunityStore.getState();
    store.setRefreshing(true);
    expect(useOpportunityStore.getState().isRefreshing).toBe(true);

    store.setRefreshing(false);
    expect(useOpportunityStore.getState().isRefreshing).toBe(false);
  });

  it("setError clears loading and refreshing", () => {
    const store = useOpportunityStore.getState();
    store.setLoading(true);
    store.setRefreshing(true);
    store.setError("Something failed");

    const state = useOpportunityStore.getState();
    expect(state.error).toBe("Something failed");
    expect(state.isLoading).toBe(false);
    expect(state.isRefreshing).toBe(false);
  });

  it("setSelectedId tracks selected opportunity", () => {
    const store = useOpportunityStore.getState();
    store.setSelectedId("opp-1");
    expect(useOpportunityStore.getState().selectedId).toBe("opp-1");

    store.setSelectedId(null);
    expect(useOpportunityStore.getState().selectedId).toBeNull();
  });

  it("reset returns to initial state", () => {
    const store = useOpportunityStore.getState();
    store.setItems([MOCK_OPP]);
    store.setSelectedId("opp-1");
    store.setError("err");

    store.reset();
    const state = useOpportunityStore.getState();
    expect(state.items).toEqual([]);
    expect(state.selectedId).toBeNull();
    expect(state.error).toBeNull();
  });
});
