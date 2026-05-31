/**
 * Tests for opportunity API client (MOBILE-003).
 *
 * Validates fetch, refresh, and action-logging API calls
 * against the /api/v1/opportunities endpoints.
 */

import { AxiosHeaders } from "axios";

import { apiClient } from "../../api/client";
import {
  fetchOpportunities,
  logOpportunityAction,
  refreshOpportunities,
} from "../../api/opportunities";
import type { OpportunityData } from "../../types/contracts";

jest.mock("../../api/client", () => ({
  apiClient: { get: jest.fn(), post: jest.fn() },
  parseApiError: jest.fn((err: unknown) => String(err)),
}));

const MOCK_OPPORTUNITY: OpportunityData = {
  id: "opp-1",
  niche: "saas",
  url: "https://example.com/post/1",
  title: "Need help with SaaS billing",
  source: "reddit",
  why_matched: "Keyword match: billing",
  relevance_score: 0.85,
  draft_reply: "Here is a helpful reply about SaaS billing...",
  edited_draft: null,
  status: "new",
  created_at: "2024-01-01T00:00:00Z",
  delivered_at: null,
};

function makeAxiosResponse<T>(data: T) {
  return {
    data,
    status: 200,
    statusText: "OK",
    headers: {},
    config: { headers: new AxiosHeaders() },
  };
}

describe("fetchOpportunities", () => {
  const mockGet = apiClient.get as jest.Mock;

  beforeEach(() => jest.clearAllMocks());

  it("fetches opportunities from /opportunities", async () => {
    mockGet.mockResolvedValueOnce(
      makeAxiosResponse([MOCK_OPPORTUNITY])
    );

    const result = await fetchOpportunities();

    expect(mockGet).toHaveBeenCalledWith("/opportunities", {
      params: { status: "new" },
    });
    expect(result).toEqual([MOCK_OPPORTUNITY]);
  });

  it("passes optional niche filter", async () => {
    mockGet.mockResolvedValueOnce(makeAxiosResponse([]));

    await fetchOpportunities({ niche: "saas" });

    expect(mockGet).toHaveBeenCalledWith("/opportunities", {
      params: { status: "new", niche: "saas" },
    });
  });

  it("propagates API errors", async () => {
    mockGet.mockRejectedValueOnce(new Error("Network error"));

    await expect(fetchOpportunities()).rejects.toThrow("Network error");
  });
});

describe("refreshOpportunities", () => {
  const mockGet = apiClient.get as jest.Mock;

  beforeEach(() => jest.clearAllMocks());

  it("sends refresh=true query param", async () => {
    mockGet.mockResolvedValueOnce(
      makeAxiosResponse([MOCK_OPPORTUNITY])
    );

    const result = await refreshOpportunities();

    expect(mockGet).toHaveBeenCalledWith("/opportunities", {
      params: { refresh: "true", status: "new" },
    });
    expect(result).toEqual([MOCK_OPPORTUNITY]);
  });
});

describe("logOpportunityAction", () => {
  const mockPost = apiClient.post as jest.Mock;

  beforeEach(() => jest.clearAllMocks());

  it("posts action to correct endpoint", async () => {
    const actionResp = {
      id: "act-1",
      opportunity_id: "opp-1",
      user_id: "usr-1",
      action_type: "archived",
      posted_url: null,
      created_at: "2024-01-01T00:00:00Z",
    };
    mockPost.mockResolvedValueOnce(makeAxiosResponse(actionResp));

    const result = await logOpportunityAction("opp-1", "archived");

    expect(mockPost).toHaveBeenCalledWith(
      "/opportunities/opp-1/actions",
      { action_type: "archived" }
    );
    expect(result).toEqual(actionResp);
  });

  it("includes posted_url when provided", async () => {
    const actionResp = {
      id: "act-2",
      opportunity_id: "opp-1",
      user_id: "usr-1",
      action_type: "posted",
      posted_url: "https://reddit.com/posted",
      created_at: "2024-01-01T00:00:00Z",
    };
    mockPost.mockResolvedValueOnce(makeAxiosResponse(actionResp));

    await logOpportunityAction(
      "opp-1",
      "posted",
      "https://reddit.com/posted"
    );

    expect(mockPost).toHaveBeenCalledWith(
      "/opportunities/opp-1/actions",
      {
        action_type: "posted",
        posted_url: "https://reddit.com/posted",
      }
    );
  });
});
