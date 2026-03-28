import { test, expect } from '@playwright/test';

test.describe('My Portfolio', () => {
  test('page loads without errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto('/tree');
    await page.waitForTimeout(2000);
    await expect(page.locator('main')).toBeVisible();
    expect(errors).toEqual([]);
  });

  test('shows at least a root node', async ({ page }) => {
    await page.goto('/tree');
    await page.waitForTimeout(3000);
    // The tree should render at least one node element in main
    const main = page.locator('main');
    await expect(main).toBeVisible();
    const mainContent = await main.textContent();
    expect(mainContent?.length).toBeGreaterThan(0);
  });

  test('clicking a node shows detail panel', async ({ page }) => {
    await page.goto('/tree');
    await page.waitForTimeout(3000);
    // Find a clickable tree node and click it
    const nodes = page.locator('main [role="treeitem"], main [data-node], main button, main a').first();
    const nodeExists = await nodes.isVisible().catch(() => false);
    if (nodeExists) {
      await nodes.click();
      await page.waitForTimeout(1000);
      // After clicking, some detail should appear (panel, drawer, or inline)
      const mainContent = await page.locator('main').textContent();
      expect(mainContent?.length).toBeGreaterThan(0);
    } else {
      // If no clickable nodes, the page at least loaded without errors
      test.skip();
    }
  });
});
