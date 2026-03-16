/**
 * Authentication setup — runs once before all tests.
 * Logs in with test credentials and saves the auth state.
 */
import { test as setup, expect } from '@playwright/test';
import path from 'path';

const AUTH_FILE = path.join(__dirname, '.auth/user.json');

const TEST_EMAIL = process.env.TEST_USER_EMAIL || 'e2e@example.com';
const TEST_PASSWORD = process.env.TEST_USER_PASSWORD || 'e2epassword123';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');

  // Wait for the login form to be visible
  await page.waitForSelector('input[type="email"]', { timeout: 10000 });

  await page.fill('input[type="email"]', TEST_EMAIL);
  await page.fill('input[type="password"]', TEST_PASSWORD);
  await page.click('button[type="submit"]');

  // Wait for redirect to dashboard after successful login
  await page.waitForURL('**/dashboard', { timeout: 15000 });
  await expect(page).toHaveURL(/dashboard/);

  // Save authentication state
  await page.context().storageState({ path: AUTH_FILE });
});
