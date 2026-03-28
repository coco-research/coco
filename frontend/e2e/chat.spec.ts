import { test, expect } from '@playwright/test';

test.describe('Chat', () => {
  test('page loads without errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto('/chat');
    await page.waitForTimeout(2000);
    await expect(page.locator('main')).toBeVisible();
    expect(errors).toEqual([]);
  });

  test('does not show Phase 7 stub', async ({ page }) => {
    await page.goto('/chat');
    await page.waitForTimeout(2000);
    const mainText = await page.locator('main').textContent();
    expect(mainText).not.toContain('Phase 7');
  });

  test('chat input is visible', async ({ page }) => {
    await page.goto('/chat');
    await page.waitForTimeout(2000);
    // Chat page should have a text input or textarea for typing messages
    const input = page.locator('main textarea, main input[type="text"]').first();
    await expect(input).toBeVisible();
  });

  test('can type a message in chat input', async ({ page }) => {
    await page.goto('/chat');
    await page.waitForTimeout(2000);
    const input = page.locator('main textarea, main input[type="text"]').first();
    await expect(input).toBeVisible();
    await input.fill('Hello CoCo');
    await expect(input).toHaveValue('Hello CoCo');
  });
});
