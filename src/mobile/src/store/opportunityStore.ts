/**
 * Opportunity state store using Zustand (MOBILE-003).
 *
 * Manages the list of opportunities fetched from the API,
 * including archive/remove and selected item state.
 *
 * Cross-module contracts:
 * - OpportunityData shape from contracts/opportunity/opportunity.py
 */

import { create } from "zustand";

import type { OpportunityData } from "../types/contracts";

interface OpportunityState {
  items: OpportunityData[];
  isLoading: boolean;
  isRefreshing: boolean;
  error: string | null;
  selectedId: string | null;
  setItems: (items: OpportunityData[]) => void;
  appendItems: (items: OpportunityData[]) => void;
  removeItem: (id: string) => void;
  setLoading: (loading: boolean) => void;
  setRefreshing: (refreshing: boolean) => void;
  setError: (error: string) => void;
  clearError: () => void;
  setSelectedId: (id: string | null) => void;
  reset: () => void;
}

const initialState = {
  items: [] as OpportunityData[],
  isLoading: false,
  isRefreshing: false,
  error: null,
  selectedId: null,
};

/** Zustand store for opportunity feed state. */
const useOpportunityStore = create<OpportunityState>((set) => ({
  ...initialState,

  setItems: (items: OpportunityData[]) =>
    set({ items, isLoading: false, isRefreshing: false, error: null }),

  appendItems: (newItems: OpportunityData[]) =>
    set((state) => ({
      items: [...state.items, ...newItems],
      isLoading: false,
    })),

  removeItem: (id: string) =>
    set((state) => ({
      items: state.items.filter((item) => item.id !== id),
    })),

  setLoading: (isLoading: boolean) => set({ isLoading }),

  setRefreshing: (isRefreshing: boolean) => set({ isRefreshing }),

  setError: (error: string) =>
    set({ error, isLoading: false, isRefreshing: false }),

  clearError: () => set({ error: null }),

  setSelectedId: (selectedId: string | null) => set({ selectedId }),

  reset: () => set({ ...initialState }),
}));

export { useOpportunityStore };
export type { OpportunityState };
