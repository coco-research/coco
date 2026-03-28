import { test, expect } from '@playwright/test';

test.describe('App Shell', () => {
  test('loads the dashboard', async ({ page }) => {
    await page.goto('/');
    // Should see sidebar with CoCo branding
    await expect(page.locator('aside')).toBeVisible();
    // Should see Dashboard heading or content
    await expect(page.locator('main')).toBeVisible();
  });

  test('sidebar navigation works', async ({ page }) => {
    await page.goto('/');
    // Click each nav item and verify we navigate
    // Visible sections: Home, Work, Intelligence
    const visibleItems = [
      { label: 'Home', url: '/' },
      { label: 'Inbox', url: '/inbox' },
      { label: 'My Portfolio', url: '/tree' },
      { label: 'Teams', url: '/projects' },
      { label: 'Todos', url: '/todos' },
      { label: 'Goals', url: '/goals' },
      { label: 'Knowledge', url: '/knowledge' },
      { label: 'Chat', url: '/chat' },
    ];
    for (const item of visibleItems) {
      await page.click(`aside a:has-text("${item.label}")`);
      await expect(page).toHaveURL(item.url);
    }

    // System section is collapsed by default — expand it
    await page.click('aside button:has-text("System")');
    const systemItems = [
      { label: 'Agent Team', url: '/agents' },
      { label: 'Costs', url: '/costs' },
      { label: 'Settings', url: '/settings' },
    ];
    for (const item of systemItems) {
      await page.click(`aside a:has-text("${item.label}")`);
      await expect(page).toHaveURL(item.url);
    }
  });

  test('dark theme is applied', async ({ page }) => {
    await page.goto('/');
    const html = page.locator('html');
    const hasDark = await html.evaluate((el) => el.classList.contains('dark'));
    expect(hasDark).toBe(true);
  });

  test.skip('Cmd+K opens command palette', async ({ page }) => {
    // Skipped: headless Chromium doesn't reliably dispatch Meta+k/Ctrl+k
    await page.goto('/');
    // Use Control+k since Meta may not work in headless Chromium
    await page.keyboard.press('Control+k');
    // The palette input placeholder is "Search pages..."
    await expect(page.locator('input[placeholder="Search pages..."]')).toBeVisible({ timeout: 3000 });
    // Type and verify filtering
    await page.keyboard.type('stat');
    await expect(page.locator('main').locator('text=Agent Team').or(page.locator('[class*="z-50"]').locator('text=Agent Team'))).toBeVisible();
    // Press escape to close
    await page.keyboard.press('Escape');
    await expect(page.locator('input[placeholder="Search pages..."]')).not.toBeVisible();
  });
});
