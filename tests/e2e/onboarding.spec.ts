/**
 * E2E tests for First-Run Setup Wizard (ONBOARD-003).
 *
 * Part 1: wizard load, step navigation, form validation,
 * plan selection, and tone step.
 */

import { expect, test } from "@playwright/test";

const BASE_URL = "http://localhost:8000";

function mockPlans(): Record<string, unknown>[] {
  return [
    {
      plan_id: "free",
      display_name: "Free",
      price_cents: 0,
      opportunities_per_day: 10,
      features: ["basic_filtering", "email_digest"],
      is_current: true,
    },
    {
      plan_id: "pro",
      display_name: "Pro",
      price_cents: 4900,
      opportunities_per_day: 100,
      features: ["advanced_filters", "draft_regeneration", "slack", "api_access"],
      is_current: false,
    },
    {
      plan_id: "premium",
      display_name: "Premium",
      price_cents: 9900,
      opportunities_per_day: 10000,
      features: ["advanced_filters", "draft_regeneration", "slack", "api_access", "team", "webhooks"],
      is_current: false,
    },
  ];
}

export function setupRoutes(
  page: import("@playwright/test").Page
): Promise<void[]> {
  return Promise.all([
    page.route(`${BASE_URL}/api/v1/onboarding/status`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ onboarding_completed: false }),
      });
    }),
    page.route(`${BASE_URL}/api/v1/onboarding/save-step`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ message: "Step saved" }),
      });
    }),
    page.route(`${BASE_URL}/api/v1/onboarding/complete`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ message: "Onboarding complete", scan_queued: true }),
      });
    }),
    page.route(`${BASE_URL}/api/v1/billing/plans`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ plans: mockPlans() }),
      });
    }),
  ]);
}

test.describe("Onboarding wizard — loads for new users", () => {
  test("wizard visible for new users", async ({ page }) => {
    await setupRoutes(page);
    await page.goto(`${BASE_URL}/onboarding`);
    await expect(page.locator(".onboarding-wizard")).toBeVisible();
    await expect(page.locator(".wizard-progress")).toContainText("Step 1 of 5");
  });

  test("displays welcome step with hero message", async ({ page }) => {
    await setupRoutes(page);
    await page.goto(`${BASE_URL}/onboarding`);
    await expect(page.locator(".step-welcome")).toBeVisible();
    await expect(page.locator(".step-welcome h2")).toContainText(
      "Let's set up BuzzReach"
    );
  });
});

test.describe("Onboarding wizard — step navigation", () => {
  test.beforeEach(async ({ page }) => {
    await setupRoutes(page);
    await page.goto(`${BASE_URL}/onboarding`);
  });

  test("next button advances to step 2", async ({ page }) => {
    await page.click("button.btn-next");
    await expect(page.locator(".wizard-progress")).toContainText("Step 2 of 5");
    await expect(page.locator(".step-product")).toBeVisible();
  });

  test("back button returns to previous step", async ({ page }) => {
    await page.click("button.btn-next");
    await expect(page.locator(".wizard-progress")).toContainText("Step 2 of 5");
    await page.click("button.btn-back");
    await expect(page.locator(".wizard-progress")).toContainText("Step 1 of 5");
  });

  test("progress indicator updates on each step", async ({ page }) => {
    for (let step = 1; step <= 4; step++) {
      await expect(page.locator(".wizard-progress")).toContainText(
        `Step ${step} of 5`
      );
      await page.click("button.btn-next");
    }
    await expect(page.locator(".wizard-progress")).toContainText("Step 5 of 5");
  });
});

test.describe("Onboarding wizard — product step validation", () => {
  test.beforeEach(async ({ page }) => {
    await setupRoutes(page);
    await page.goto(`${BASE_URL}/onboarding`);
    await page.click("button.btn-next");
  });

  test("product URL validated as non-empty valid URL", async ({ page }) => {
    await page.locator("#wizardProductUrl").fill("not-a-url");
    await page.click("button.btn-next");
    await expect(page.locator(".field-error")).toContainText("valid URL");
  });

  test("valid product URL allows advancement", async ({ page }) => {
    await page.locator("#wizardProductUrl").fill("https://myproduct.com");
    await page.locator("#wizardPitch").fill("A great product");
    await page.click("button.btn-next");
    await expect(page.locator(".wizard-progress")).toContainText("Step 3 of 5");
  });
});

test.describe("Onboarding wizard — keywords step", () => {
  test.beforeEach(async ({ page }) => {
    await setupRoutes(page);
    await page.goto(`${BASE_URL}/onboarding`);
    await page.click("button.btn-next");
    await page.locator("#wizardProductUrl").fill("https://myproduct.com");
    await page.locator("#wizardPitch").fill("A great product");
    await page.click("button.btn-next");
  });

  test("keywords form accepts multiple entries", async ({ page }) => {
    await expect(page.locator(".step-audience")).toBeVisible();
    const keywordsInput = page.locator("#wizardKeywords");
    await keywordsInput.fill("react\ntypescript\nnextjs");
    await page.click("button.btn-next");
    await expect(page.locator(".wizard-progress")).toContainText("Step 4 of 5");
  });
});

test.describe("Onboarding wizard — tone step", () => {
  test.beforeEach(async ({ page }) => {
    await setupRoutes(page);
    await page.goto(`${BASE_URL}/onboarding`);
    await page.click("button.btn-next");
    await page.locator("#wizardProductUrl").fill("https://myproduct.com");
    await page.locator("#wizardPitch").fill("A great product");
    await page.click("button.btn-next");
    await page.locator("#wizardKeywords").fill("react\ntypescript");
    await page.click("button.btn-next");
  });

  test("tone selection shows examples", async ({ page }) => {
    await expect(page.locator(".step-tone")).toBeVisible();
    await expect(page.locator(".tone-examples")).toBeVisible();
    await page.click('[data-tone="casual"]');
    await expect(page.locator(".tone-example-text")).toBeVisible();
  });
});

test.describe("Onboarding wizard — plan step", () => {
  test.beforeEach(async ({ page }) => {
    await setupRoutes(page);
    await page.goto(`${BASE_URL}/onboarding`);
    await page.click("button.btn-next");
    await page.locator("#wizardProductUrl").fill("https://myproduct.com");
    await page.locator("#wizardPitch").fill("A great product");
    await page.click("button.btn-next");
    await page.locator("#wizardKeywords").fill("react\ntypescript");
    await page.click("button.btn-next");
    await page.click("button.btn-next");
  });

  test("plan comparison shows all three plans", async ({ page }) => {
    await expect(page.locator(".step-plan")).toBeVisible();
    await expect(page.locator(".plan-card")).toHaveCount(3);
  });

  test("plan features listed side-by-side", async ({ page }) => {
    const freeCard = page.locator('.plan-card[data-plan="free"]');
    await expect(freeCard).toBeVisible();
    await expect(freeCard.locator(".plan-features")).toBeVisible();
  });
});
