import { test, expect } from '@playwright/test';

test.describe('Collaboration', () => {
  test('workflow templates API returns data', async ({ page }) => {
    const response = await page.request.get('/api/workflow-templates');
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();
    expect(data.length).toBeGreaterThan(0);
  });
});
