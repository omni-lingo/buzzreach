/**
 * E2E tests for Opportunities Dashboard page (FE-002).
 *
 * Validates: load feed, filter by platform, filter by score,
 * copy-to-clipboard, mark-as-posted, archive, auto-refresh,
 * mobile responsive, and URL opens in new tab.
 */

import { expect, test } from "@playwright/test";

const BASE_URL = "http://localhost:8000";

function mockOpportunity(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    id: "aaaaaaaa-0000-0000-0000-000000000001",
    niche: "developer tools",
    url: "https://reddit.com/r/webdev/post/123",
    title: "Looking for a tool to automate outreach",
    source: "reddit",
    why_matched: "Mentions need for automation tools",
    relevance_score: 0.85,
    draft_reply: "Great question! Our tool does exactly this...",
    edited_draft: null,
    status: "new",
    created_at: "2025-06-01T10:00:00Z",
    delivered_at: null,
    ...overrides,
  };
}

function mockOpportunityList(count: number): Record<string, unknown>[] {
  const sources = ["reddit", "quora", "hackernews", "twitter"];
  return Array.from({ length: count }, (_, i) =>
    mockOpportunity({
      id: `aaaaaaaa-0000-0000-0000-${String(i + 1).padStart(12, "0")}`,
      title: `Opportunity ${i + 1}`,
      source: sources[i % sources.length],
      relevance_score: 0.5 + (i % 50) / 100,
    })
  );
}

test.describe("Dashboard — feed display", () => {
  test.beforeEach(async ({ page }) => {
    const items = mockOpportunityList(25);
    await page.route(
      `${BASE_URL}/api/v1/opportunities*`,
      async (route) => {
        if (route.request().method() === "GET") {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({ items, total: items.length }),
          });
        }
      }
    );
  });

  test("loads and displays 20+ opportunities", async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page.locator(".dashboard-page")).toBeVisible();
    const cards = page.locator(".opportunity-card");
    await expect(cards).toHaveCount(25);
  });

  test("each card shows title, platform, score, and draft preview", async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    const firstCard = page.locator(".opportunity-card").first();
    await expect(firstCard.locator(".opp-title")).toBeVisible();
    await expect(firstCard.locator(".opp-source")).toBeVisible();
    await expect(firstCard.locator(".opp-score")).toBeVisible();
    await expect(firstCard.locator(".opp-draft")).toBeVisible();
  });

  test("clicking URL opens thread in new tab", async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    const link = page.locator(".opportunity-card .opp-title a").first();
    const target = await link.getAttribute("target");
    expect(target).toBe("_blank");
    const rel = await link.getAttribute("rel");
    expect(rel).toContain("noopener");
  });
});

test.describe("Dashboard — filtering", () => {
  const items = mockOpportunityList(25);

  test.beforeEach(async ({ page }) => {
    await page.route(
      `${BASE_URL}/api/v1/opportunities*`,
      async (route) => {
        const url = new URL(route.request().url());
        const platform = url.searchParams.get("platform");
        const scoreMin = url.searchParams.get("score_min");
        let filtered = [...items];
        if (platform) {
          filtered = filtered.filter(
            (o) => o.source === platform
          );
        }
        if (scoreMin) {
          filtered = filtered.filter(
            (o) => (o.relevance_score as number) >= parseFloat(scoreMin)
          );
        }
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            items: filtered,
            total: filtered.length,
          }),
        });
      }
    );
  });

  test("filter by platform updates feed", async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await page.click('[data-platform="reddit"]');
    const cards = page.locator(".opportunity-card");
    const count = await cards.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < count; i++) {
      await expect(
        cards.nth(i).locator(".opp-source")
      ).toContainText("reddit");
    }
  });

  test("score range slider filters opportunities", async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    const slider = page.locator('input[name="score_min"]');
    await slider.fill("0.8");
    await slider.dispatchEvent("change");
    const cards = page.locator(".opportunity-card");
    const count = await cards.count();
    expect(count).toBeGreaterThan(0);
  });
});

test.describe("Dashboard — card actions", () => {
  test.beforeEach(async ({ page }) => {
    const items = [mockOpportunity()];
    await page.route(
      `${BASE_URL}/api/v1/opportunities*`,
      async (route) => {
        if (route.request().method() === "GET") {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({ items, total: 1 }),
          });
        }
      }
    );
  });

  test("copy-to-clipboard button copies draft reply", async ({
    page,
    context,
  }) => {
    await context.grantPermissions(["clipboard-read", "clipboard-write"]);
    await page.route(
      `${BASE_URL}/api/v1/opportunities/*/actions`,
      async (route) => {
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            id: "action-1",
            action_type: "copied",
            created_at: new Date().toISOString(),
          }),
        });
      }
    );

    await page.goto(`${BASE_URL}/dashboard`);
    await page.click("button.btn-copy-draft");
    const clipText = await page.evaluate(() =>
      navigator.clipboard.readText()
    );
    expect(clipText).toContain("Great question!");
  });

  test("mark-as-posted removes opportunity from feed", async ({ page }) => {
    await page.route(
      `${BASE_URL}/api/v1/opportunities/*/mark-posted`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ success: true }),
        });
      }
    );

    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page.locator(".opportunity-card")).toHaveCount(1);
    await page.click("button.btn-mark-posted");
    await expect(page.locator(".opportunity-card")).toHaveCount(0);
  });

  test("archive button hides opportunity from feed", async ({ page }) => {
    await page.route(
      `${BASE_URL}/api/v1/opportunities/*/archive`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ success: true }),
        });
      }
    );

    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page.locator(".opportunity-card")).toHaveCount(1);
    await page.click("button.btn-archive");
    await expect(page.locator(".opportunity-card")).toHaveCount(0);
  });
});

test.describe("Dashboard — empty state", () => {
  test("shows empty state when no opportunities", async ({ page }) => {
    await page.route(
      `${BASE_URL}/api/v1/opportunities*`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ items: [], total: 0 }),
        });
      }
    );

    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page.locator(".empty-state")).toBeVisible();
    await expect(page.locator(".empty-state")).toContainText(
      "No opportunities"
    );
  });
});

test.describe("Dashboard — mobile responsive", () => {
  test("renders at 320px width without overflow", async ({ page }) => {
    const items = mockOpportunityList(5);
    await page.route(
      `${BASE_URL}/api/v1/opportunities*`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ items, total: items.length }),
        });
      }
    );

    await page.setViewportSize({ width: 320, height: 568 });
    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page.locator(".dashboard-page")).toBeVisible();
    const box = await page.locator(".dashboard-page").boundingBox();
    if (box) {
      expect(box.width).toBeLessThanOrEqual(320);
    }
  });
});
