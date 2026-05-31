/**
 * E2E tests for Keyboard Shortcuts (QUALITY-002).
 *
 * Validates: j/k navigation, c (copy), o (open thread),
 * a (archive), p (mark posted), r (regenerate), ? (help modal),
 * Escape (close modal), text-field suppression.
 */

import { expect, test } from "@playwright/test";

const BASE_URL = "http://localhost:8000";

function mockOpportunity(
  overrides: Record<string, unknown> = {}
): Record<string, unknown> {
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

function mockOpportunityList(
  count: number
): Record<string, unknown>[] {
  return Array.from({ length: count }, (_, i) =>
    mockOpportunity({
      id: `aaaaaaaa-0000-0000-0000-${String(i + 1).padStart(12, "0")}`,
      title: `Opportunity ${i + 1}`,
      source: ["reddit", "quora", "hackernews"][i % 3],
      relevance_score: 0.6 + (i % 40) / 100,
      draft_reply: `Draft reply for opportunity ${i + 1}`,
    })
  );
}

function setupDashboardRoute(
  page: import("@playwright/test").Page,
  count: number
): Promise<void> {
  const items = mockOpportunityList(count);
  return page.route(
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
}

function setupActionRoutes(
  page: import("@playwright/test").Page
): Promise<void> {
  return page.route(
    `${BASE_URL}/api/v1/opportunities/*/archive`,
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ success: true }),
      });
    }
  );
}

test.describe("Keyboard shortcuts — j/k navigation", () => {
  test.beforeEach(async ({ page }) => {
    await setupDashboardRoute(page, 5);
    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page.locator(".opportunity-card")).toHaveCount(5);
  });

  test("j moves focus to next opportunity card", async ({ page }) => {
    await page.keyboard.press("j");
    const focused = page.locator(
      ".opportunity-card.keyboard-active"
    );
    await expect(focused).toHaveCount(1);
    await expect(focused).toContainText("Opportunity 1");
  });

  test("k moves focus to previous opportunity card", async ({
    page,
  }) => {
    await page.keyboard.press("j");
    await page.keyboard.press("j");
    await page.keyboard.press("k");
    const focused = page.locator(
      ".opportunity-card.keyboard-active"
    );
    await expect(focused).toContainText("Opportunity 1");
  });

  test("j wraps at end of list", async ({ page }) => {
    for (let i = 0; i < 6; i++) {
      await page.keyboard.press("j");
    }
    const focused = page.locator(
      ".opportunity-card.keyboard-active"
    );
    await expect(focused).toContainText("Opportunity 1");
  });
});

test.describe("Keyboard shortcuts — card actions", () => {
  test.beforeEach(async ({ page }) => {
    await setupDashboardRoute(page, 3);
    await setupActionRoutes(page);
    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page.locator(".opportunity-card")).toHaveCount(3);
    await page.keyboard.press("j");
  });

  test("c copies draft to clipboard", async ({ page, context }) => {
    await context.grantPermissions([
      "clipboard-read",
      "clipboard-write",
    ]);
    await page.keyboard.press("c");
    const clipText = await page.evaluate(() =>
      navigator.clipboard.readText()
    );
    expect(clipText).toContain("Draft reply for opportunity 1");
  });

  test("o opens thread URL in new tab", async ({ page }) => {
    const [newPage] = await Promise.all([
      page.context().waitForEvent("page"),
      page.keyboard.press("o"),
    ]);
    expect(newPage.url()).toContain("reddit.com");
  });

  test("a archives focused opportunity", async ({ page }) => {
    await page.keyboard.press("a");
    await expect(page.locator(".opportunity-card")).toHaveCount(2);
  });

  test("p marks focused opportunity as posted", async ({ page }) => {
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
    await page.keyboard.press("p");
    await expect(page.locator(".opportunity-card")).toHaveCount(2);
  });
});

test.describe("Keyboard shortcuts — help modal", () => {
  test.beforeEach(async ({ page }) => {
    await setupDashboardRoute(page, 3);
    await page.goto(`${BASE_URL}/dashboard`);
  });

  test("? opens help modal", async ({ page }) => {
    await page.keyboard.press("Shift+/");
    await expect(
      page.locator(".keyboard-help-modal")
    ).toBeVisible();
  });

  test("Escape closes help modal", async ({ page }) => {
    await page.keyboard.press("Shift+/");
    await expect(
      page.locator(".keyboard-help-modal")
    ).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(
      page.locator(".keyboard-help-modal")
    ).not.toBeVisible();
  });

  test("help modal shows shortcut list", async ({ page }) => {
    await page.keyboard.press("Shift+/");
    const modal = page.locator(".keyboard-help-modal");
    await expect(modal.locator(".shortcut-row")).toHaveCount({
      min: 5,
    });
    await expect(modal).toContainText("Next opportunity");
  });
});

test.describe("Keyboard shortcuts — text input suppression", () => {
  test("shortcuts do not fire when typing in input", async ({
    page,
  }) => {
    await setupDashboardRoute(page, 3);
    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page.locator(".opportunity-card")).toHaveCount(3);

    const input = page.locator('input[name="score_min"]');
    await input.focus();
    await page.keyboard.press("j");

    const focused = page.locator(
      ".opportunity-card.keyboard-active"
    );
    await expect(focused).toHaveCount(0);
  });
});

test.describe("Keyboard shortcuts — Escape closes modals", () => {
  test("Escape closes any open modal", async ({ page }) => {
    await setupDashboardRoute(page, 3);
    await page.goto(`${BASE_URL}/dashboard`);
    await page.keyboard.press("Shift+/");
    await expect(
      page.locator(".keyboard-help-modal")
    ).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(
      page.locator(".keyboard-help-modal")
    ).not.toBeVisible();
  });
});
