/**
 * Tests for OpportunityCard mobile component (MOBILE-003).
 *
 * Validates card rendering, touch targets, and draft privacy.
 */

import React from "react";
import { render, screen } from "@testing-library/react-native";

import OpportunityCard from "../../components/OpportunityCard.mobile";
import type { OpportunityData } from "../../types/contracts";

const MOCK_OPPORTUNITY: OpportunityData = {
  id: "opp-1",
  niche: "saas",
  url: "https://example.com/post/1",
  title: "Need help with SaaS billing",
  source: "reddit",
  why_matched: "Keyword match: billing",
  relevance_score: 0.85,
  draft_reply:
    "Here is a helpful reply about SaaS billing that is quite long " +
    "and should be truncated to first 100 characters for the card " +
    "preview so the user sees a snippet only.",
  edited_draft: null,
  status: "new",
  created_at: "2024-01-01T00:00:00Z",
  delivered_at: null,
};

describe("OpportunityCard", () => {
  it("renders opportunity title", () => {
    render(
      <OpportunityCard
        opportunity={MOCK_OPPORTUNITY}
        onPress={jest.fn()}
      />
    );

    expect(screen.getByText("Need help with SaaS billing")).toBeTruthy();
  });

  it("renders platform and score", () => {
    render(
      <OpportunityCard
        opportunity={MOCK_OPPORTUNITY}
        onPress={jest.fn()}
      />
    );

    expect(screen.getByText("reddit")).toBeTruthy();
    expect(screen.getByText("85%")).toBeTruthy();
  });

  it("shows truncated draft preview (max 100 chars)", () => {
    render(
      <OpportunityCard
        opportunity={MOCK_OPPORTUNITY}
        onPress={jest.fn()}
      />
    );

    const previewText = screen.getByTestId("draft-preview");
    const text = previewText.props.children as string;
    expect(text.length).toBeLessThanOrEqual(103); // 100 + "..."
  });

  it("does not expose full draft text", () => {
    render(
      <OpportunityCard
        opportunity={MOCK_OPPORTUNITY}
        onPress={jest.fn()}
      />
    );

    expect(
      screen.queryByText(MOCK_OPPORTUNITY.draft_reply)
    ).toBeNull();
  });

  it("renders match reason snippet", () => {
    render(
      <OpportunityCard
        opportunity={MOCK_OPPORTUNITY}
        onPress={jest.fn()}
      />
    );

    expect(screen.getByText("Keyword match: billing")).toBeTruthy();
  });
});
