import { test, expect } from '@playwright/test';

const pages = [
  { path: '/', title: 'Dashboard' },
  { path: '/projects', title: 'Projects' },
  { path: '/agents', title: 'Agent Team' },
  { path: '/knowledge', title: 'Knowledge' },
  { path: '/inbox', title: 'Inbox' },
  { path: '/todos', title: 'Todo' },
  { path: '/goals', title: 'Goals' },
  { path: '/chat', title: 'CoCo' },
  { path: '/costs', title: 'Cost' },
  { path: '/activity', title: 'Activity' },
  { path: '/tree', title: 'My Portfolio' },
  { path: '/settings', title: 'Settings' },
];

for (const { path, title } of pages) {
  test(`${path} loads without errors`, async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto(path);
    await page.waitForTimeout(2000);
    // Page should have content in main area
    await expect(page.locator('main')).toBeVisible();
    // No JS errors
    expect(errors).toEqual([]);
  });
}
