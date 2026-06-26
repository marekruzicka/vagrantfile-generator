import { expect, test } from '@playwright/test'

async function themeColor(page) {
  return page.locator('meta[name="theme-color"]').getAttribute('content')
}

test.describe('dashboard theme toggle', () => {
  test('header toggle switches and persists dark mode after sign in', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('vfg-theme', 'light')
    })

    await page.goto('/')
    await expect(
      page.getByRole('heading', { name: /your vagrant projects/i })
    ).toBeVisible()

    const cookieBanner = page.locator('#vfg-cookie-banner')
    if (await cookieBanner.isVisible().catch(() => false)) {
      await cookieBanner.getByRole('button', { name: /^dismiss$/i }).click()
    }

    await expect(page.locator('html')).not.toHaveClass(/\bdark\b/)
    await expect.poll(() => themeColor(page)).toBe('#3b82f6')

    const toggle = page.getByRole('button', { name: /toggle dark mode/i })
    await expect(toggle).toBeVisible()
    await toggle.click()

    await expect(page.locator('html')).toHaveClass(/\bdark\b/)
    await expect.poll(() => themeColor(page)).toBe('#1e293b')
    await expect
      .poll(() => page.evaluate(() => localStorage.getItem('vfg-theme')))
      .toBe('dark')

    await toggle.click()

    await expect(page.locator('html')).not.toHaveClass(/\bdark\b/)
    await expect.poll(() => themeColor(page)).toBe('#3b82f6')
    await expect
      .poll(() => page.evaluate(() => localStorage.getItem('vfg-theme')))
      .toBe('light')
  })
})
