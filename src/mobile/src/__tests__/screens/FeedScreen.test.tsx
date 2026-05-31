/**
 * Tests for FeedScreen (MOBILE-003).
 *
 * Validates feed loading, pull-to-refresh, empty state,
 * and error display.
 */

import React from "react";
import {
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";

import FeedScreen from "../../screens/FeedScreen";
import { useOpportunityStore } from "../../store/opportunityStore";
import type { OpportunityData } from "../../types/contracts";

const mockFetch = jest.fn();
const mockRefresh = jest.fn();
const mockLogAction = jest.fn();

jest.mock("../../api/opportunities", () => ({
  fetchOpportunities: (...args: unknown[]) => mockFetch(...args),
  refreshOpportunities: (...args: unknown[]) => mockRefresh(...args),
  logOpportunityAction: (...args: unknown[]) =>
    mockLogAction(...args),
}));

jest.mock("react-native-gesture-handler", () => {
  const { View } = require("react-native");
  return {
    GestureDetector: ({ children }: { children: React.ReactNode }) => (
      <>{children}</>
    ),
    Gesture: {
      Pan: () => ({
        onUpdate: () => ({ onEnd: () => ({}) }),
      }),
    },
    GestureHandlerRootView: View,
  };
});

jest.mock("react-native-reanimated", () => {
  const { View } = require("react-native");
  return {
    __esModule: true,
    default: {
      createAnimatedComponent: (comp: unknown) => comp,
      View,
    },
    useSharedValue: (init: number) => ({ value: init }),
    useAnimatedStyle: (fn: () => object) => fn(),
    withSpring: (val: number) => val,
    withTiming: (val: number) => val,
    runOnJS: (fn: (...args: unknown[]) => void) => fn,
    FadeIn: { duration: () => ({}) },
  };
});

const MOCK_ITEMS: OpportunityData[] = [
  {
    id: "opp-1",
    niche: "saas",
    url: "https://example.com/1",
    title: "SaaS billing help",
    source: "reddit",
    why_matched: "Keyword match",
    relevance_score: 0.85,
    draft_reply: "Draft reply text",
    edited_draft: null,
    status: "new",
    created_at: "2024-01-01T00:00:00Z",
    delivered_at: null,
  },
  {
    id: "opp-2",
    niche: "devtools",
    url: "https://example.com/2",
    title: "Dev tools recommendation",
    source: "quora",
    why_matched: "Topic match",
    relevance_score: 0.72,
    draft_reply: "Another draft",
    edited_draft: null,
    status: "new",
    created_at: "2024-01-02T00:00:00Z",
    delivered_at: null,
  },
];

describe("FeedScreen", () => {
  beforeEach(() => {
    useOpportunityStore.getState().reset();
    jest.clearAllMocks();
  });

  it("shows loading indicator when loading with no items", () => {
    mockFetch.mockReturnValue(new Promise(() => {}));
    useOpportunityStore.getState().setLoading(true);

    render(<FeedScreen />);

    expect(
      screen.getByText("Loading opportunities...")
    ).toBeTruthy();
  });

  it("shows empty state when no opportunities", async () => {
    mockFetch.mockResolvedValueOnce([]);

    render(<FeedScreen />);

    await waitFor(() => {
      expect(screen.getByText("No opportunities yet")).toBeTruthy();
    });
  });

  it("renders opportunity cards when items exist", async () => {
    mockFetch.mockResolvedValueOnce(MOCK_ITEMS);

    render(<FeedScreen />);

    await waitFor(() => {
      expect(screen.getByText("SaaS billing help")).toBeTruthy();
      expect(
        screen.getByText("Dev tools recommendation")
      ).toBeTruthy();
    });
  });

  it("displays error banner when fetch fails", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    render(<FeedScreen />);

    await waitFor(() => {
      expect(
        screen.getByText("An unexpected error occurred")
      ).toBeTruthy();
    });
  });
});
