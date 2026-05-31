/**
 * Tests for OpportunityDetail modal (MOBILE-003).
 *
 * Validates full detail display, button rendering,
 * and action button accessibility.
 */

import React from "react";
import {
  fireEvent,
  render,
  screen,
} from "@testing-library/react-native";

import OpportunityDetail from "../../screens/OpportunityDetail";
import type { OpportunityData } from "../../types/contracts";

jest.mock("expo-clipboard", () => ({
  setStringAsync: jest.fn().mockResolvedValue(true),
}));

jest.mock("expo-linking", () => ({
  openURL: jest.fn().mockResolvedValue(true),
}));

jest.mock("../../api/opportunities", () => ({
  logOpportunityAction: jest.fn().mockResolvedValue({
    id: "act-1",
    opportunity_id: "opp-1",
    user_id: "usr-1",
    action_type: "copied",
    posted_url: null,
    created_at: "2024-01-01T00:00:00Z",
  }),
}));

const MOCK_OPPORTUNITY: OpportunityData = {
  id: "opp-1",
  niche: "saas",
  url: "https://example.com/post/1",
  title: "Need help with SaaS billing",
  source: "reddit",
  why_matched: "Keyword match: billing",
  relevance_score: 0.85,
  draft_reply:
    "Here is a helpful and detailed reply about SaaS billing " +
    "that the user would want to copy and paste.",
  edited_draft: null,
  status: "new",
  created_at: "2024-01-01T00:00:00Z",
  delivered_at: null,
};

describe("OpportunityDetail", () => {
  const onClose = jest.fn();
  const onArchive = jest.fn();
  const onMarkPosted = jest.fn();

  beforeEach(() => jest.clearAllMocks());

  it("renders full opportunity title", () => {
    render(
      <OpportunityDetail
        opportunity={MOCK_OPPORTUNITY}
        visible={true}
        onClose={onClose}
        onArchive={onArchive}
        onMarkPosted={onMarkPosted}
      />
    );

    expect(
      screen.getByText("Need help with SaaS billing")
    ).toBeTruthy();
  });

  it("shows full draft reply text", () => {
    render(
      <OpportunityDetail
        opportunity={MOCK_OPPORTUNITY}
        visible={true}
        onClose={onClose}
        onArchive={onArchive}
        onMarkPosted={onMarkPosted}
      />
    );

    expect(
      screen.getByText(MOCK_OPPORTUNITY.draft_reply)
    ).toBeTruthy();
  });

  it("displays platform and score", () => {
    render(
      <OpportunityDetail
        opportunity={MOCK_OPPORTUNITY}
        visible={true}
        onClose={onClose}
        onArchive={onArchive}
        onMarkPosted={onMarkPosted}
      />
    );

    expect(screen.getByText("reddit")).toBeTruthy();
    expect(screen.getByText("85%")).toBeTruthy();
  });

  it("displays score reason", () => {
    render(
      <OpportunityDetail
        opportunity={MOCK_OPPORTUNITY}
        visible={true}
        onClose={onClose}
        onArchive={onArchive}
        onMarkPosted={onMarkPosted}
      />
    );

    expect(screen.getByText("Keyword match: billing")).toBeTruthy();
  });

  it("renders Copy to Clipboard button", () => {
    render(
      <OpportunityDetail
        opportunity={MOCK_OPPORTUNITY}
        visible={true}
        onClose={onClose}
        onArchive={onArchive}
        onMarkPosted={onMarkPosted}
      />
    );

    expect(screen.getByText("Copy to Clipboard")).toBeTruthy();
  });

  it("renders Open in Browser button", () => {
    render(
      <OpportunityDetail
        opportunity={MOCK_OPPORTUNITY}
        visible={true}
        onClose={onClose}
        onArchive={onArchive}
        onMarkPosted={onMarkPosted}
      />
    );

    expect(screen.getByText("Open in Browser")).toBeTruthy();
  });

  it("renders Mark as Posted button", () => {
    render(
      <OpportunityDetail
        opportunity={MOCK_OPPORTUNITY}
        visible={true}
        onClose={onClose}
        onArchive={onArchive}
        onMarkPosted={onMarkPosted}
      />
    );

    expect(screen.getByText("Mark as Posted")).toBeTruthy();
  });

  it("renders Archive button", () => {
    render(
      <OpportunityDetail
        opportunity={MOCK_OPPORTUNITY}
        visible={true}
        onClose={onClose}
        onArchive={onArchive}
        onMarkPosted={onMarkPosted}
      />
    );

    expect(screen.getByText("Archive")).toBeTruthy();
  });

  it("calls onClose when close button pressed", () => {
    render(
      <OpportunityDetail
        opportunity={MOCK_OPPORTUNITY}
        visible={true}
        onClose={onClose}
        onArchive={onArchive}
        onMarkPosted={onMarkPosted}
      />
    );

    fireEvent.press(screen.getByTestId("close-button"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("copies draft to clipboard on button press", async () => {
    const Clipboard = require("expo-clipboard") as {
      setStringAsync: jest.Mock;
    };

    render(
      <OpportunityDetail
        opportunity={MOCK_OPPORTUNITY}
        visible={true}
        onClose={onClose}
        onArchive={onArchive}
        onMarkPosted={onMarkPosted}
      />
    );

    fireEvent.press(screen.getByText("Copy to Clipboard"));

    expect(Clipboard.setStringAsync).toHaveBeenCalledWith(
      MOCK_OPPORTUNITY.draft_reply
    );
  });

  it("opens browser on Open in Browser press", () => {
    const Linking = require("expo-linking") as {
      openURL: jest.Mock;
    };

    render(
      <OpportunityDetail
        opportunity={MOCK_OPPORTUNITY}
        visible={true}
        onClose={onClose}
        onArchive={onArchive}
        onMarkPosted={onMarkPosted}
      />
    );

    fireEvent.press(screen.getByText("Open in Browser"));

    expect(Linking.openURL).toHaveBeenCalledWith(
      MOCK_OPPORTUNITY.url
    );
  });

  it("does not render when not visible", () => {
    render(
      <OpportunityDetail
        opportunity={MOCK_OPPORTUNITY}
        visible={false}
        onClose={onClose}
        onArchive={onArchive}
        onMarkPosted={onMarkPosted}
      />
    );

    expect(
      screen.queryByText("Need help with SaaS billing")
    ).toBeNull();
  });
});
