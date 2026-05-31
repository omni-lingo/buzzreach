/**
 * Tests for MOBILE-004: OpportunityActions component.
 *
 * Covers:
 * - Button rendering and accessibility
 * - Copy Draft clipboard integration
 * - Open Thread URL launch integration
 * - Toast display on copy
 * - Action logging via FEAT-003
 *
 * Utility tests in test_mobile_utils.tsx.
 */

import React from "react";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";

import { OpportunityActions } from "../src/mobile/src/components/OpportunityActions";
import type { OpportunityData } from "../src/mobile/src/types/contracts";

const mockSetStringAsync = jest.fn().mockResolvedValue(true);

jest.mock("expo-clipboard", () => ({
  setStringAsync: (...args: unknown[]) => mockSetStringAsync(...args),
  getStringAsync: jest.fn().mockResolvedValue(""),
}));

const mockOpenURL = jest.fn().mockResolvedValue(true);
const mockCanOpenURL = jest.fn().mockResolvedValue(false);

jest.mock("expo-linking", () => ({
  openURL: (...args: unknown[]) => mockOpenURL(...args),
  canOpenURL: (...args: unknown[]) => mockCanOpenURL(...args),
}));

jest.mock("../src/mobile/src/api/opportunities", () => ({
  logOpportunityAction: jest.fn().mockResolvedValue({
    id: "act-1",
    opportunity_id: "opp-1",
    user_id: "usr-1",
    action_type: "copied",
    posted_url: null,
    created_at: "2024-01-01T00:00:00Z",
  }),
}));

const MOCK_OPP: OpportunityData = {
  id: "opp-1",
  niche: "saas",
  url: "https://www.reddit.com/r/saas/comments/abc123/post",
  title: "Need SaaS billing help",
  source: "reddit",
  why_matched: "Keyword match: billing",
  relevance_score: 0.85,
  draft_reply: "Here is a helpful reply about billing.",
  edited_draft: null,
  status: "new",
  created_at: "2024-01-01T00:00:00Z",
  delivered_at: null,
};

describe("OpportunityActions", () => {
  const onCopyComplete = jest.fn();
  const onOpenComplete = jest.fn();

  beforeEach(() => jest.clearAllMocks());

  it("renders Copy Draft button", () => {
    render(
      <OpportunityActions
        opportunity={MOCK_OPP}
        includeFooter={false}
        onCopyComplete={onCopyComplete}
        onOpenComplete={onOpenComplete}
      />
    );
    expect(screen.getByText("Copy Draft")).toBeTruthy();
  });

  it("renders Open Thread button", () => {
    render(
      <OpportunityActions
        opportunity={MOCK_OPP}
        includeFooter={false}
        onCopyComplete={onCopyComplete}
        onOpenComplete={onOpenComplete}
      />
    );
    expect(screen.getByText("Open Thread")).toBeTruthy();
  });

  it("Copy Draft button has accessible tap area", () => {
    render(
      <OpportunityActions
        opportunity={MOCK_OPP}
        includeFooter={false}
        onCopyComplete={onCopyComplete}
        onOpenComplete={onOpenComplete}
      />
    );
    const btn = screen.getByTestId("copy-draft-button");
    expect(btn).toBeTruthy();
    expect(btn.props.accessibilityRole).toBe("button");
  });

  it("Open Thread button has accessible tap area", () => {
    render(
      <OpportunityActions
        opportunity={MOCK_OPP}
        includeFooter={false}
        onCopyComplete={onCopyComplete}
        onOpenComplete={onOpenComplete}
      />
    );
    const btn = screen.getByTestId("open-thread-button");
    expect(btn).toBeTruthy();
    expect(btn.props.accessibilityRole).toBe("button");
  });

  it("copies draft to clipboard on press", async () => {
    render(
      <OpportunityActions
        opportunity={MOCK_OPP}
        includeFooter={false}
        onCopyComplete={onCopyComplete}
        onOpenComplete={onOpenComplete}
      />
    );

    await act(async () => {
      fireEvent.press(screen.getByText("Copy Draft"));
    });

    expect(mockSetStringAsync).toHaveBeenCalledWith(
      MOCK_OPP.draft_reply
    );
  });

  it("uses edited_draft when available", async () => {
    const oppWithEdit: OpportunityData = {
      ...MOCK_OPP,
      edited_draft: "Edited reply text",
    };

    render(
      <OpportunityActions
        opportunity={oppWithEdit}
        includeFooter={false}
        onCopyComplete={onCopyComplete}
        onOpenComplete={onOpenComplete}
      />
    );

    await act(async () => {
      fireEvent.press(screen.getByText("Copy Draft"));
    });

    expect(mockSetStringAsync).toHaveBeenCalledWith(
      "Edited reply text"
    );
  });

  it("includes footer when enabled", async () => {
    render(
      <OpportunityActions
        opportunity={MOCK_OPP}
        includeFooter={true}
        onCopyComplete={onCopyComplete}
        onOpenComplete={onOpenComplete}
      />
    );

    await act(async () => {
      fireEvent.press(screen.getByText("Copy Draft"));
    });

    expect(mockSetStringAsync).toHaveBeenCalledWith(
      `${MOCK_OPP.draft_reply}\n\nPosted via BuzzReach`
    );
  });

  it("shows toast after copy", async () => {
    render(
      <OpportunityActions
        opportunity={MOCK_OPP}
        includeFooter={false}
        onCopyComplete={onCopyComplete}
        onOpenComplete={onOpenComplete}
      />
    );

    await act(async () => {
      fireEvent.press(screen.getByText("Copy Draft"));
    });

    await waitFor(() => {
      expect(
        screen.getByText("Copied to clipboard")
      ).toBeTruthy();
    });
  });

  it("calls onCopyComplete after copy", async () => {
    render(
      <OpportunityActions
        opportunity={MOCK_OPP}
        includeFooter={false}
        onCopyComplete={onCopyComplete}
        onOpenComplete={onOpenComplete}
      />
    );

    await act(async () => {
      fireEvent.press(screen.getByText("Copy Draft"));
    });

    expect(onCopyComplete).toHaveBeenCalledTimes(1);
  });

  it("opens URL on Open Thread press", async () => {
    render(
      <OpportunityActions
        opportunity={MOCK_OPP}
        includeFooter={false}
        onCopyComplete={onCopyComplete}
        onOpenComplete={onOpenComplete}
      />
    );

    await act(async () => {
      fireEvent.press(screen.getByText("Open Thread"));
    });

    expect(mockOpenURL).toHaveBeenCalled();
  });

  it("calls onOpenComplete after open", async () => {
    render(
      <OpportunityActions
        opportunity={MOCK_OPP}
        includeFooter={false}
        onCopyComplete={onCopyComplete}
        onOpenComplete={onOpenComplete}
      />
    );

    await act(async () => {
      fireEvent.press(screen.getByText("Open Thread"));
    });

    expect(onOpenComplete).toHaveBeenCalledTimes(1);
  });

  it("logs copied action via API", async () => {
    const { logOpportunityAction } = require(
      "../src/mobile/src/api/opportunities"
    ) as { logOpportunityAction: jest.Mock };

    render(
      <OpportunityActions
        opportunity={MOCK_OPP}
        includeFooter={false}
        onCopyComplete={onCopyComplete}
        onOpenComplete={onOpenComplete}
      />
    );

    await act(async () => {
      fireEvent.press(screen.getByText("Copy Draft"));
    });

    expect(logOpportunityAction).toHaveBeenCalledWith(
      "opp-1",
      "copied"
    );
  });
});
