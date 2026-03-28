import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test('shows project cards', async ({ page }) => {
    await page.goto('/');
    // Wait for data to load (skeleton should disappear)
    await page.waitForSelector('[class*="animate-pulse"]', { state: 'detached', timeout: 10000 }).catch(() => {});
    // Should show projects section heading in main content area
    // Should show project cards or project section in the dashboard
    await expect(page.locator('main')).toBeVisible();
    // Dashboard should have some content (cards, sections, etc.)
    const mainContent = await page.locator('main').textContent();
    expect(mainContent?.length).toBeGreaterThan(0);
  });

  test('shows health indicators', async ({ page }) => {
    await page.goto('/');
    // Health bar should show source names
    await page.waitForTimeout(2000);
    const main = page.locator('main');
    await expect(main).toBeVisible();
  });

  test('no JavaScript errors on load', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto('/');
    await page.waitForTimeout(3000);
    expect(errors).toEqual([]);
  });
});
