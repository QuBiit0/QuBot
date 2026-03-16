/**
 * E2E tests for authentication flows:
 * - Login page renders
 * - Invalid credentials show error
 * - Unauthenticated access redirects to login
 * - Register flow works
 */
import { test, expect } from '@playwright/test';

// These tests do NOT depend on the setup project (no storageState)
test.use({ storageState: { cookies: [], origins: [] } });

test.describe('Login page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('renders login form', async ({ page }) => {
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('shows error on invalid credentials', async ({ page }) => {
    await page.fill('input[type="email"]', 'wrong@example.com');
    await page.fill('input[type="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Should stay on login page and show an error
    await expect(page).toHaveURL(/login/);
    // The error message should appear somewhere on the page
    await expect(
      page.locator('text=/invalid|incorrect|failed|error/i').first()
    ).toBeVisible({ timeout: 5000 });
  });

  test('redirects to login when accessing protected route unauthenticated', async ({
    page,
  }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/login/);
  });

  test('shows register link', async ({ page }) => {
    const registerLink = page.locator('a[href*="register"]');
    await expect(registerLink).toBeVisible();
  });
});

test.describe('Register page', () => {
  test('renders register form', async ({ page }) => {
    await page.goto('/register');
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('shows password mismatch error', async ({ page }) => {
    await page.goto('/register');
    await page.fill('input[name="username"]', 'newuser');
    await page.fill('input[type="email"]', 'new@example.com');

    // Fill password fields with mismatching values
    const passwordInputs = page.locator('input[type="password"]');
    await passwordInputs.nth(0).fill('password123');
    await passwordInputs.nth(1).fill('different456');
    await page.click('button[type="submit"]');

    // Should show a mismatch error
    await expect(
      page.locator('text=/match|mismatch/i').first()
    ).toBeVisible({ timeout: 5000 });
  });
});
