/**
 * E2E test: Landing page scroll-to-dismiss behavior.
 *
 * Verifies that the login card overlay dismisses on scroll
 * and that the "Learn more" button also dismisses it.
 */
import { expect, test } from '@playwright/test'

test.describe('Landing page scroll-to-dismiss', () => {
  test('shows login card on initial visit and dismisses on scroll', async ({
    page,
  }) => {
    // Mock deployment mode to public.
    await page.route('**/api/config/deployment-mode', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ mode: 'public' }),
      })
    })

    // Mock all other API calls to avoid noise.
    await page.route('**/api/**', async (route) => {
      const url = route.request().url()
      // Let the footer API through so the page renders fully.
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

    // Clear any stored auth state.
    await page.addInitScript(() => {
      localStorage.clear()
    })

    // ---- Act 1: Initial visit - login card is visible ----
    await page.goto('/landing.html')
    await page.waitForLoadState('networkidle')

    // Login card and email OTP form should be visible.
    const loginCard = page.locator('.login-card-enter')
    await expect(loginCard).toBeVisible({ timeout: 10_000 })
    await expect(page.getByLabel(/email address/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /send login code/i })).toBeVisible()

    // "Learn more" hint should be visible.
    const learnMore = page.getByText(/learn more about vagrantfile generator/i)
    await expect(learnMore).toBeVisible()

    // Landing content should be blurred.
    const blurredBg = page.locator('.landing-bg.blurred')
    await expect(blurredBg).toBeVisible()

    // ---- Act 2: Scroll down — login card dismisses ----
    await page.mouse.wheel(0, 500)

    // Login card should disappear.
    await expect(loginCard).not.toBeVisible({ timeout: 5_000 })

    // Blur should be removed from landing content.
    await expect(blurredBg).not.toBeVisible({ timeout: 5_000 })

    // Sticky header bar should appear with "Sign In" button.
    const stickyBar = page.locator('.sticky-bar-enter')
    await expect(stickyBar).toBeVisible({ timeout: 5_000 })
    await expect(stickyBar.getByRole('link', { name: /sign in/i })).toBeVisible()

    // Landing content should be fully visible.
    await expect(page.getByText(/everything you need/i)).toBeVisible()

    // ---- Act 3: Scroll back up — sticky bar stays, card doesn't return ----
    await page.mouse.wheel(0, -500)
    await page.waitForTimeout(500)

    // Sticky bar should still be visible (doesn't revert on scroll up).
    await expect(stickyBar).toBeVisible()

    // Login card should NOT reappear.
    await expect(loginCard).not.toBeVisible()
  })

  test('"Learn more" button dismisses login card without scrolling', async ({
    page,
  }) => {
    // Mock deployment mode to public.
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

    await page.addInitScript(() => {
      localStorage.clear()
    })

    await page.goto('/landing.html')
    await page.waitForLoadState('networkidle')

    const loginCard = page.locator('.login-card-enter')
    await expect(loginCard).toBeVisible({ timeout: 10_000 })

    // ---- Click "Learn more" ----
    await page.getByText(/learn more about vagrantfile generator/i).click()

    // Login card should disappear.
    await expect(loginCard).not.toBeVisible({ timeout: 5_000 })

    // Sticky header bar should appear.
    const stickyBar = page.locator('.sticky-bar-enter')
    await expect(stickyBar).toBeVisible({ timeout: 5_000 })

    // Features section should be visible.
    await expect(page.getByText(/multiple vms/i).first()).toBeVisible()
  })

  test('"Sign In" in sticky bar navigates to login page', async ({ page }) => {
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

    await page.addInitScript(() => {
      localStorage.clear()
    })

    await page.goto('/landing.html')
    await page.waitForLoadState('networkidle')

    // Scroll to dismiss login card.
    await page.mouse.wheel(0, 500)
    const stickyBar = page.locator('.sticky-bar-enter')
    await expect(stickyBar).toBeVisible({ timeout: 5_000 })

    // Click "Sign In" in sticky bar.
    await stickyBar.getByRole('link', { name: /sign in/i }).click()

    // Should navigate to the standalone login page.
    await expect(page).toHaveURL(/\/views\/login\/login\.html$/, { timeout: 10_000 })
  })

  test('features section is present and all 6 feature cards render', async ({
    page,
  }) => {
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

    await page.addInitScript(() => {
      localStorage.clear()
    })

    await page.goto('/landing.html')
    await page.waitForLoadState('networkidle')

    // Dismiss login card via "Learn more".
    await page.getByText(/learn more about vagrantfile generator/i).click()

    // Verify all 6 feature cards.
    const featureCards = page.locator('.card.flex.items-start.space-x-4')
    await expect(featureCards).toHaveCount(6)

    // Spot-check specific features using heading role (avoids matching description text).
    await expect(page.getByRole('heading', { name: 'Multiple VMs' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Advanced Networking' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Shell Provisioners' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Vagrant Plugins' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Vagrant Triggers' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Real-time Validation' })).toBeVisible()
  })
})
