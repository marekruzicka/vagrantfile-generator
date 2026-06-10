import { expect, test } from '@playwright/test'
import { SettingsPage } from './pages/SettingsPage'

test.describe('6. Global Settings: Plugins', () => {
  test('6.1-6.4 view, create, and delete a user-owned plugin', async ({ page }) => {
    const settings = new SettingsPage(page)
    const pluginName = `e2e-plugin-${Date.now()}`

    await settings.goto()
    try {
      await expect(page.getByRole('heading', { name: /vagrant plugins/i })).toBeVisible()
      await expect(page.getByRole('button', { name: /refresh plugins/i })).toBeVisible()
      await settings.addPlugin(pluginName)
      const card = settings.resourceCard(pluginName)
      await expect(card).toContainText('E2E plugin description')
      await expect(card).toContainText(/Active|Deprecated/)
      await expect(card).toContainText(/1\.2\.3|v1\.2\.3/)
    } finally {
      await settings.safeDeleteResource(pluginName, /delete plugin/i)
    }
  })

  test('6.5 invalid plugin submission keeps the modal open', async ({ page }) => {
    const settings = new SettingsPage(page)
    await settings.goto()

    await page.getByRole('button', { name: /add plugin|add first plugin/i }).first().click()
    const dialog = page
      .getByRole('heading', { name: /add new plugin/i })
      .locator('xpath=ancestor::div[contains(@class, "bg-white")][1]')
    await expect(dialog).toBeVisible()
    await dialog.getByRole('button', { name: /^add plugin$/i }).click()
    await expect(dialog).toBeVisible()
  })
})
