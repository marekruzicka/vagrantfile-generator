import { expect, test } from '@playwright/test'
import { SettingsPage } from './pages/SettingsPage'

test.describe('8. Global Settings: Provisioners', () => {
  test('8.1-8.4 view, create, edit, and delete a shell provisioner', async ({ page }) => {
    const settings = new SettingsPage(page)
    const provisionerName = `e2e-provisioner-${Date.now()}`

    await settings.goto()
    try {
      await expect(page.getByRole('heading', { name: /global provisioners/i })).toBeVisible()
      await settings.addProvisioner(provisionerName, 'echo E2E provisioner')
      const card = settings.resourceCard(provisionerName)
      await expect(card).toContainText('E2E provisioner description')
      await expect(card).toContainText(/shell|always/i)

      await card.hover()
      await card.locator('button:visible').first().click()
      const dialog = page
        .getByRole('heading', { name: /edit provisioner/i })
        .locator('xpath=ancestor::div[contains(@class, "bg-white")][1]')
      await expect(dialog).toBeVisible()
      await dialog.locator('xpath=.//label[contains(normalize-space(.), "Description")]/following::textarea[1]').fill('Updated E2E provisioner description')
      await dialog.locator('xpath=.//label[contains(normalize-space(.), "Shell Script")]/following::textarea[1]').fill('echo updated provisioner')
      await dialog.locator('select').last().selectOption('once')
      await dialog.getByRole('button', { name: /^update provisioner$/i }).click()
      await expect(dialog).toBeHidden()
      await expect(settings.resourceCard(provisionerName)).toContainText('Updated E2E provisioner description')
    } finally {
      await settings.safeDeleteResource(provisionerName, /delete provisioner/i)
    }
  })
})
