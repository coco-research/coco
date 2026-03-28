import { test, expect } from '@playwright/test';

test.describe('Agents', () => {
  test('can open create agent dialog', async ({ page }) => {
    await page.goto('/agents');
    // Click New Agent button
    await page.click('button:has-text("New Agent")');
    // Dialog should open with "New Agent" title
    await expect(page.locator('text=New Agent').last()).toBeVisible();
    // Fill the name field (placeholder is "e.g. refactor-auth")
    await page.fill('input[placeholder="e.g. refactor-auth"]', 'Test Agent');
    // Fill task description
    await page.fill('textarea[placeholder="What should this agent do?"]', 'Test task');
    // Verify submit button is visible
    await expect(page.locator('button:has-text("Create & Launch")')).toBeVisible();
  });
});
