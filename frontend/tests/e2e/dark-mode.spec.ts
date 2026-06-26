import { expect, test } from '@playwright/test'

async function mockLandingApis(page) {
  await page.route('**/api/config/deployment-mode', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ mode: 'public' }),
    })
  })

  await page.route('**/api/**', async (route) => {
    const url = route.request().url()
    if (url.includes('/api/footer/')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'success', files: [], excluded: [], errors: [] }),
      })
      return
    }
    await route.abort('aborted')
  })
}

async function themeColor(page) {
  return page.locator('meta[name="theme-color"]').getAttribute('content')
}

test.describe('dark mode theme', () => {
  test.beforeEach(async ({ page }) => {
    await mockLandingApis(page)
  })

  test('stored dark preference applies html class and theme color', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('vfg-theme', 'dark')
    })

    await page.goto('/landing.html')

    await expect(page.locator('html')).toHaveClass(/\bdark\b/)
    await expect.poll(() => themeColor(page)).toBe('#1e293b')
  })

  test('stored light preference removes html class and sets light theme color', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'dark' })
    await page.addInitScript(() => {
      localStorage.setItem('vfg-theme', 'light')
    })

    await page.goto('/landing.html')

    await expect(page.locator('html')).not.toHaveClass(/\bdark\b/)
    await expect.poll(() => themeColor(page)).toBe('#3b82f6')
  })

  test('defaults to OS dark preference when no theme is stored', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'dark' })
    await page.addInitScript(() => {
      localStorage.removeItem('vfg-theme')
    })

    await page.goto('/landing.html')

    await expect(page.locator('html')).toHaveClass(/\bdark\b/)
    await expect.poll(() => themeColor(page)).toBe('#1e293b')
  })

  test('theme API toggles and persists preference', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('vfg-theme', 'light')
    })

    await page.goto('/landing.html')
    await page.evaluate(() => window.__theme.toggle())

    await expect(page.locator('html')).toHaveClass(/\bdark\b/)
    await expect.poll(() => themeColor(page)).toBe('#1e293b')
    await expect
      .poll(() => page.evaluate(() => localStorage.getItem('vfg-theme')))
      .toBe('dark')
  })
})
