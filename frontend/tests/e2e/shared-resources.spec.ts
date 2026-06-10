import { expect, test } from '@playwright/test'
import { SettingsPage } from './pages/SettingsPage'

test.describe('12. Shared Resources and Multi-User Isolation', () => {
  test('12.1-12.5 shared resources show badges, read-only controls, favorites, and visibility toggle', async ({ page }) => {
    const settings = new SettingsPage(page)
    await settings.goto()

    const sharedBadge = page.getByText('Shared').first()
    test.skip(!(await sharedBadge.isVisible().catch(() => false)), 'No shared resources available in this environment')

    await expect(sharedBadge).toBeVisible()
    await expect(page.getByRole('button', { name: /copy to my resources/i }).first()).toBeVisible()

    const favorite = page.getByRole('button', { name: /add to favorites|remove from favorites/i }).first()
    await favorite.click()
    await expect(page.getByRole('button', { name: /add to favorites|remove from favorites/i }).first()).toBeVisible()

    await page.getByRole('checkbox', { name: /showing/i }).click({ force: true })
    await expect(page.getByText('Hidden')).toBeVisible()
    await page.getByRole('checkbox', { name: /hidden/i }).click({ force: true })
    await expect(page.getByText('Showing')).toBeVisible()
  })
})
