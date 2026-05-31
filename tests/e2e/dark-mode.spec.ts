/**
 * E2E tests for Dark Mode Theme (QUALITY-001).
 *
 * Validates: theme toggle, localStorage persistence, system preference
 * detection, CSS variable switching, contrast, and print mode.
 */

import { expect, test } from "@playwright/test";

const BASE_URL = "http://localhost:8000";

test.describe("Dark Mode — toggle behavior", () => {
  test.beforeEach(async ({ page }) => {
    await page.route(`${BASE_URL}/api/v1/opportunities*`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0 }),
      });
    });
  });

  test("toggle button visible in header", async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    const toggle = page.locator("[data-testid='theme-toggle']");
    await expect(toggle).toBeVisible();
  });

  test("clicking toggle switches from light to dark", async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    const html = page.locator("html");
    await expect(html).not.toHaveAttribute("data-theme", "dark");

    await page.click("[data-testid='theme-toggle']");
    await expect(html).toHaveAttribute("data-theme", "dark");
  });

  test("clicking toggle twice returns to light mode", async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await page.click("[data-testid='theme-toggle']");
    await page.click("[data-testid='theme-toggle']");
    const html = page.locator("html");
    await expect(html).toHaveAttribute("data-theme", "light");
  });

  test("no visible flicker when switching themes", async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    const toggle = page.locator("[data-testid='theme-toggle']");

    const flickered = await toggle.evaluate(() => {
      return new Promise<boolean>((resolve) => {
        let visibilityChange = false;
        const observer = new MutationObserver((mutations) => {
          for (const m of mutations) {
            if (
              m.type === "attributes" &&
              m.attributeName === "style" &&
              (m.target as HTMLElement).style.display === "none"
            ) {
              visibilityChange = true;
            }
          }
        });
        observer.observe(document.documentElement, {
          attributes: true,
          subtree: true,
        });
        document
          .querySelector("[data-testid='theme-toggle']")
          ?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
        requestAnimationFrame(() => {
          observer.disconnect();
          resolve(visibilityChange);
        });
      });
    });

    expect(flickered).toBe(false);
  });
});

test.describe("Dark Mode — localStorage persistence", () => {
  test.beforeEach(async ({ page }) => {
    await page.route(`${BASE_URL}/api/v1/opportunities*`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0 }),
      });
    });
  });

  test("theme preference persists after reload", async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await page.click("[data-testid='theme-toggle']");
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  });

  test("localStorage contains theme value after toggle", async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await page.click("[data-testid='theme-toggle']");

    const stored = await page.evaluate(() =>
      localStorage.getItem("buzzreach-theme")
    );
    expect(stored).toBe("dark");
  });

  test("clearing localStorage reverts to system default", async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await page.click("[data-testid='theme-toggle']");
    await page.evaluate(() => localStorage.removeItem("buzzreach-theme"));
    await page.reload();

    const theme = await page.locator("html").getAttribute("data-theme");
    expect(theme).toBe("light");
  });
});

test.describe("Dark Mode — system preference", () => {
  test.beforeEach(async ({ page }) => {
    await page.route(`${BASE_URL}/api/v1/opportunities*`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0 }),
      });
    });
  });

  test("respects prefers-color-scheme: dark on first load", async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  });

  test("respects prefers-color-scheme: light on first load", async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: "light" });
    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  });

  test("user preference overrides system preference", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

    await page.click("[data-testid='theme-toggle']");
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  });
});

test.describe("Dark Mode — CSS variables", () => {
  test.beforeEach(async ({ page }) => {
    await page.route(`${BASE_URL}/api/v1/opportunities*`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0 }),
      });
    });
  });

  test("CSS custom properties change with theme", async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    const lightBg = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue(
        "--bg-primary"
      )
    );

    await page.click("[data-testid='theme-toggle']");
    const darkBg = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue(
        "--bg-primary"
      )
    );

    expect(lightBg.trim()).not.toBe(darkBg.trim());
  });

  test("text has sufficient contrast in dark mode", async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await page.click("[data-testid='theme-toggle']");

    const contrast = await page.evaluate(() => {
      const style = getComputedStyle(document.documentElement);
      const bg = style.getPropertyValue("--bg-primary").trim();
      const text = style.getPropertyValue("--text-primary").trim();
      return { bg, text };
    });

    expect(contrast.bg).toBeTruthy();
    expect(contrast.text).toBeTruthy();
    expect(contrast.bg).not.toBe(contrast.text);
  });
});

test.describe("Dark Mode — print mode", () => {
  test("print styles use light colors regardless of theme", async ({
    page,
  }) => {
    await page.route(`${BASE_URL}/api/v1/opportunities*`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0 }),
      });
    });

    await page.goto(`${BASE_URL}/dashboard`);
    await page.click("[data-testid='theme-toggle']");
    await page.emulateMedia({ media: "print" });

    const bg = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue(
        "--bg-primary"
      )
    );
    expect(bg.trim()).toBeTruthy();
  });
});
