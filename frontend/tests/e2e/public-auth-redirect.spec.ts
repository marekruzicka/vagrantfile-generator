/**
 * E2E test: Public-mode unauthenticated redirect without protected API fetch noise.
 *
 * Verifies the shouldLoadData() guard added to app.js prevents in-flight
 * API calls from aborting when main.js's DOMContentLoaded handler redirects
 * to login in public mode with no auth token.
 */
import { expect, test } from '@playwright/test'

const PROTECTED_ENDPOINTS = [
  '/api/config/preferences',
  '/api/projects',
  '/api/boxes',
  '/api/plugins',
  '/api/provisioners',
  '/api/triggers',
]

test.describe('Public-mode unauthenticated redirect', () => {
  test('redirects to login without making protected API calls or console errors', async ({
    page,
  }) => {
    // ---- Arrange -----------------------------------------------------------

    // Track which protected endpoints get called.
    const calledEndpoints = new Set<string>()

    // Single catch-all route: mock deployment mode and spy on protected endpoints.
    await page.route('**/api/**', async (route) => {
      const url = route.request().url()

      // Mock deployment-mode to return "public".
      if (url.includes('/api/config/deployment-mode')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ mode: 'public' }),
        })
        return
      }

      // Spy on protected endpoints: record and abort.
      const matched = PROTECTED_ENDPOINTS.find((ep) => url.includes(ep))
      if (matched) {
        calledEndpoints.add(matched)
        // Abort — the shouldLoadData guard should have prevented this call.
        await route.abort('aborted')
        return
      }

      // All other API calls pass through to the real backend.
      await route.continue()
    })

    // Collect uncaught console errors.
    const consoleErrors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text())
      }
    })

    // Clear any previously persisted storage state so we start unauthenticated.
    // addInitScript runs before any page script, preventing the race.
    await page.addInitScript(() => {
      localStorage.clear()
    })

    // ---- Act ---------------------------------------------------------------

    await page.goto('/')

    // Wait for the auth redirect to settle.
    await page.waitForLoadState('networkidle')

    // ---- Assert ------------------------------------------------------------

    // 1. We should end up on the login page.
    await expect(page).toHaveURL(/\/views\/login\/login\.html$/, { timeout: 15_000 })

    // 2. No protected endpoint should have been called.
    expect(calledEndpoints.size).toBe(0)

    // 3. No uncaught console errors from aborted data-loading API fetches.
    // (HTML partial-loading errors during redirect are pre-existing and unrelated.)
    const dataLoadingErrors = consoleErrors.filter(
      (err) =>
        (err.includes('Failed to fetch') || err.includes('aborted') || err.includes('AbortError')) &&
        PROTECTED_ENDPOINTS.some((ep) => err.includes(ep)),
    )
    expect(dataLoadingErrors).toEqual([])
  })
})
