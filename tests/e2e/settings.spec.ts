/**
 * E2E tests for Settings & Account Settings pages (FE-001).
 *
 * Validates: load -> edit -> save -> reload -> verify flow,
 * API key regeneration, password change, and form validation.
 */

import { expect, test } from "@playwright/test";

const BASE_URL = "http://localhost:8000";

function mockSettingsPayload(): Record<string, unknown> {
  return {
    product_url: "https://example.com",
    one_line_pitch: "Best SaaS tool",
    keywords: ["react", "typescript"],
    tone: "professional",
    delivery_email: "user@example.com",
    slack_webhook_url: "",
    delivery_frequency: "daily",
    platform_preferences: ["reddit", "quora"],
    exclude_domains: ["spam.com"],
    api_key_masked: "bz_****abcd",
    email: "user@example.com",
    created_at: "2025-01-15T10:00:00Z",
    usage_stats: { opportunities_found: 42, drafts_generated: 30 },
  };
}

test.describe("Settings page", () => {
  test.beforeEach(async ({ page }) => {
    await page.route(`${BASE_URL}/api/v1/settings`, async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockSettingsPayload()),
        });
      } else if (route.request().method() === "POST") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ message: "Settings saved" }),
        });
      }
    });
  });

  test("loads current user config from API", async ({ page }) => {
    await page.goto(`${BASE_URL}/settings`);
    await expect(page.locator(".settings-page")).toBeVisible();
    await expect(page.locator("#productUrl")).toHaveValue(
      "https://example.com"
    );
    await expect(page.locator("#oneLinePitch")).toHaveValue("Best SaaS tool");
  });

  test("user can update keywords and save", async ({ page }) => {
    await page.goto(`${BASE_URL}/settings`);
    const keywordsInput = page.locator("#keywords");
    await keywordsInput.clear();
    await keywordsInput.fill("react\ntypescript\nnextjs");
    await page.click("button.btn-save");
    await expect(page.locator(".success-banner")).toBeVisible();
  });

  test("user can update tone and delivery settings", async ({ page }) => {
    await page.goto(`${BASE_URL}/settings`);
    await page.selectOption("#tone", "casual");
    await page.selectOption("#deliveryFrequency", "hourly");
    await page.click("button.btn-save");
    await expect(page.locator(".success-banner")).toBeVisible();
  });

  test("form validation prevents empty keywords", async ({ page }) => {
    await page.goto(`${BASE_URL}/settings`);
    const keywordsInput = page.locator("#keywords");
    await keywordsInput.clear();
    await page.click("button.btn-save");
    await expect(page.locator(".field-error")).toBeVisible();
  });

  test("form validation prevents invalid email", async ({ page }) => {
    await page.goto(`${BASE_URL}/settings`);
    const emailInput = page.locator("#deliveryEmail");
    await emailInput.clear();
    await emailInput.fill("not-an-email");
    await page.click("button.btn-save");
    await expect(page.locator(".field-error")).toBeVisible();
  });

  test("edit -> save -> reload -> verify roundtrip", async ({ page }) => {
    await page.goto(`${BASE_URL}/settings`);
    const pitchInput = page.locator("#oneLinePitch");
    await pitchInput.clear();
    await pitchInput.fill("Updated pitch text");
    await page.click("button.btn-save");
    await expect(page.locator(".success-banner")).toBeVisible();

    await page.route(`${BASE_URL}/api/v1/settings`, async (route) => {
      if (route.request().method() === "GET") {
        const updated = mockSettingsPayload();
        updated.one_line_pitch = "Updated pitch text";
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(updated),
        });
      }
    });

    await page.reload();
    await expect(pitchInput).toHaveValue("Updated pitch text");
  });
});

test.describe("API key management", () => {
  test.beforeEach(async ({ page }) => {
    await page.route(`${BASE_URL}/api/v1/settings`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockSettingsPayload()),
      });
    });
  });

  test("API key regeneration works", async ({ page }) => {
    await page.route(
      `${BASE_URL}/api/v1/settings/regenerate-key`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ api_key: "bz_newkey1234" }),
        });
      }
    );

    await page.goto(`${BASE_URL}/settings`);
    await page.click("button.btn-regenerate-key");
    const confirmBtn = page.locator("button.btn-confirm-regenerate");
    await confirmBtn.click();
    await expect(page.locator(".api-key-display")).toContainText("bz_new");
  });
});

test.describe("Account Settings page", () => {
  test.beforeEach(async ({ page }) => {
    await page.route(`${BASE_URL}/api/v1/settings`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockSettingsPayload()),
      });
    });
  });

  test("displays user email as read-only", async ({ page }) => {
    await page.goto(`${BASE_URL}/account`);
    const emailField = page.locator("#accountEmail");
    await expect(emailField).toHaveValue("user@example.com");
    await expect(emailField).toBeDisabled();
  });

  test("password change requires current password", async ({ page }) => {
    await page.goto(`${BASE_URL}/account`);
    const newPwInput = page.locator("#newPassword");
    const confirmPwInput = page.locator("#confirmNewPassword");
    await newPwInput.fill("NewPass123!");
    await confirmPwInput.fill("NewPass123!");
    await page.click("button.btn-change-password");
    await expect(page.locator(".field-error")).toContainText(
      "Current password is required"
    );
  });

  test("password change succeeds with valid inputs", async ({ page }) => {
    await page.route(
      `${BASE_URL}/api/v1/password/change`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ message: "Password changed" }),
        });
      }
    );

    await page.goto(`${BASE_URL}/account`);
    await page.locator("#currentPassword").fill("OldPass123!");
    await page.locator("#newPassword").fill("NewPass123!");
    await page.locator("#confirmNewPassword").fill("NewPass123!");
    await page.click("button.btn-change-password");
    await expect(page.locator(".success-banner")).toBeVisible();
  });

  test("API key visibility toggle and copy", async ({ page }) => {
    await page.goto(`${BASE_URL}/account`);
    const keyDisplay = page.locator(".api-key-value");
    await expect(keyDisplay).toContainText("****");
    await page.click("button.btn-toggle-key");
    await expect(keyDisplay).not.toContainText("****");
    await expect(page.locator("button.btn-copy-key")).toBeVisible();
  });

  test("mobile responsive at 320px width", async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 568 });
    await page.goto(`${BASE_URL}/account`);
    await expect(page.locator(".account-settings-page")).toBeVisible();
    const box = await page
      .locator(".account-settings-page")
      .boundingBox();
    if (box) {
      expect(box.width).toBeLessThanOrEqual(320);
    }
  });
});
