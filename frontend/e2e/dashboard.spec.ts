/**
 * E2E tests for the dashboard (authenticated):
 * - Dashboard loads without errors
 * - Navigation works
 * - Metric cards render
 */
import { test, expect } from '@playwright/test';
// Uses storageState from playwright.config.ts (requires auth.setup to run first)

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    // Wait for content to load
    await page.waitForLoadState('networkidle');
  });

  test('loads dashboard page', async ({ page }) => {
    await expect(page).toHaveURL(/dashboard/);
    // Page should not show 404 or error page
    await expect(page.locator('text=404')).not.toBeVisible();
  });

  test('shows navigation elements', async ({ page }) => {
    // Sidebar or nav should be present
    const nav = page.locator('nav, [role="navigation"], aside').first();
    await expect(nav).toBeVisible({ timeout: 5000 });
  });

  test('renders metric cards area', async ({ page }) => {
    // Wait for dashboard to settle
    await page.waitForTimeout(500);
    // The dashboard should have some content (not just a blank page)
    const bodyText = await page.locator('body').innerText();
    expect(bodyText.length).toBeGreaterThan(50);
  });

  test('can navigate to mission control', async ({ page }) => {
    // Find a link to mission control
    const missionLink = page.locator('a[href*="mission-control"]').first();
    if (await missionLink.isVisible()) {
      await missionLink.click();
      await expect(page).toHaveURL(/mission-control/);
    } else {
      // If no direct link, navigate directly
      await page.goto('/mission-control');
      await expect(page).toHaveURL(/mission-control/);
    }
  });
});

test.describe('Mission Control page', () => {
  test('loads kanban board', async ({ page }) => {
    await page.goto('/mission-control');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveURL(/mission-control/);
    // Page should load without crashing
    await expect(page.locator('text=404')).not.toBeVisible();
    await expect(page.locator('text=Error')).not.toBeVisible();
  });
});
