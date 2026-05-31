/**
 * E2E tests for First-Run Setup Wizard (ONBOARD-003).
 *
 * Part 2: completion flow, skip functionality, mobile responsive,
 * and tutorial tooltip on dashboard.
 */

import { expect, test } from "@playwright/test";

const BASE_URL = "http://localhost:8000";

function mockPlans(): Record<string, unknown>[] {
  return [
    { plan_id: "free", display_name: "Free", price_cents: 0, opportunities_per_day: 10, features: ["basic_filtering", "email_digest"], is_current: true },
    { plan_id: "pro", display_name: "Pro", price_cents: 4900, opportunities_per_day: 100, features: ["advanced_filters", "draft_regeneration", "slack", "api_access"], is_current: false },
    { plan_id: "premium", display_name: "Premium", price_cents: 9900, opportunities_per_day: 10000, features: ["advanced_filters", "draft_regeneration", "slack", "api_access", "team", "webhooks"], is_current: false },
  ];
}

function fulfillJson(route: { fulfill: (opts: Record<string, unknown>) => Promise<void> }, body: unknown): Promise<void> {
  return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
}

function setupRoutes(page: import("@playwright/test").Page): Promise<void[]> {
  return Promise.all([
    page.route(`${BASE_URL}/api/v1/onboarding/status`, (r) => fulfillJson(r, { onboarding_completed: false })),
    page.route(`${BASE_URL}/api/v1/onboarding/save-step`, (r) => fulfillJson(r, { message: "Step saved" })),
    page.route(`${BASE_URL}/api/v1/onboarding/complete`, (r) => fulfillJson(r, { message: "Onboarding complete", scan_queued: true })),
    page.route(`${BASE_URL}/api/v1/billing/plans`, (r) => fulfillJson(r, { plans: mockPlans() })),
  ]);
}

test.describe("Onboarding wizard — completion", () => {
  test("config saved and initial scan triggered after step 5", async ({
    page,
  }) => {
    await setupRoutes(page);
    let completeCalled = false;
    await page.route(
      `${BASE_URL}/api/v1/onboarding/complete`,
      async (route) => {
        completeCalled = true;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            message: "Onboarding complete",
            scan_queued: true,
          }),
        });
      }
    );

    await page.goto(`${BASE_URL}/onboarding`);
    await page.click("button.btn-next");
    await page.locator("#wizardProductUrl").fill("https://myproduct.com");
    await page.locator("#wizardPitch").fill("A great product");
    await page.click("button.btn-next");
    await page.locator("#wizardKeywords").fill("react");
    await page.click("button.btn-next");
    await page.click("button.btn-next");
    await page.click("button.btn-finish");

    expect(completeCalled).toBe(true);
    await expect(page.locator(".onboarding-complete")).toBeVisible();
    await expect(page.locator(".onboarding-complete")).toContainText(
      "Your first opportunities coming soon"
    );
  });
});

test.describe("Onboarding wizard — skip functionality", () => {
  test("steps 1-4 have skip button", async ({ page }) => {
    await setupRoutes(page);
    await page.goto(`${BASE_URL}/onboarding`);

    for (let step = 0; step < 4; step++) {
      await expect(page.locator("button.btn-skip")).toBeVisible();
      await page.click("button.btn-skip");
    }
    await expect(page.locator("button.btn-skip")).not.toBeVisible();
  });

  test("skip uses defaults and advances", async ({ page }) => {
    await setupRoutes(page);
    await page.goto(`${BASE_URL}/onboarding`);
    await page.click("button.btn-skip");
    await expect(page.locator(".wizard-progress")).toContainText(
      "Step 2 of 5"
    );
  });
});

test.describe("Onboarding wizard — mobile responsive", () => {
  test("renders at 320px width in vertical layout", async ({ page }) => {
    await setupRoutes(page);
    await page.setViewportSize({ width: 320, height: 568 });
    await page.goto(`${BASE_URL}/onboarding`);
    await expect(page.locator(".onboarding-wizard")).toBeVisible();
    const box = await page.locator(".onboarding-wizard").boundingBox();
    if (box) {
      expect(box.width).toBeLessThanOrEqual(320);
    }
  });
});

test.describe("Onboarding wizard — tutorial tooltip", () => {
  test("tutorial tooltip shows on dashboard after wizard", async ({
    page,
  }) => {
    await setupRoutes(page);
    await page.route(
      `${BASE_URL}/api/v1/onboarding/status`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ onboarding_completed: true }),
        });
      }
    );
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
    await expect(page.locator(".tutorial-tooltip")).toBeVisible();
  });
});
