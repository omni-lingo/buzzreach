/**
 * Opportunity state store using Zustand (MOBILE-001).
 *
 * Manages the list of opportunities fetched from the API.
 * Full implementation deferred to MOBILE-003 (Opportunity Feed).
 *
 * Cross-module contracts:
 * - OpportunityData shape from contracts/opportunity/opportunity.py
 */

import { create } from "zustand";

import type { OpportunityData } from "../types/contracts";

interface OpportunityState {
  items: OpportunityData[];
  isLoading: boolean;
  error: string | null;
  setItems: (items: OpportunityData[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string) => void;
  clearError: () => void;
  reset: () => void;
}

const initialState = {
  items: [] as OpportunityData[],
  isLoading: false,
  error: null,
};

/** Zustand store for opportunity feed state. */
const useOpportunityStore = create<OpportunityState>((set) => ({
  ...initialState,

  setItems: (items: OpportunityData[]) =>
    set({ items, isLoading: false, error: null }),

  setLoading: (isLoading: boolean) => set({ isLoading }),

  setError: (error: string) => set({ error, isLoading: false }),

  clearError: () => set({ error: null }),

  reset: () => set({ ...initialState }),
}));

export { useOpportunityStore };
export type { OpportunityState };
