import { expect, test } from '@playwright/test'
import { SettingsPage } from './pages/SettingsPage'

test.describe('8. Global Settings: Provisioners', () => {
  test('8.1-8.4 view, create, and delete a shell provisioner', async ({ page }) => {
    const settings = new SettingsPage(page)
    const provisionerName = `e2e-provisioner-${Date.now()}`

    await settings.goto()
    try {
      await expect(page.getByRole('heading', { name: /global provisioners/i })).toBeVisible()
      await settings.addProvisioner(provisionerName, 'echo E2E provisioner')
      const card = settings.resourceCard(provisionerName)
      await expect(card).toContainText('E2E provisioner description')
      await expect(card).toContainText(/shell|always/i)
    } finally {
      await settings.safeDeleteResource(provisionerName, /delete provisioner/i)
    }
  })
})
