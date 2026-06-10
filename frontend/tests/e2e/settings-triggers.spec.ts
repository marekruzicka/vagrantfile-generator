import { expect, test } from '@playwright/test'
import { SettingsPage } from './pages/SettingsPage'

test.describe('10. Global Settings: Triggers', () => {
  test('10.1-10.5 view, create, and delete a host trigger', async ({ page }) => {
    const settings = new SettingsPage(page)
    const triggerName = `e2e-trigger-${Date.now()}`

    await settings.goto()
    try {
      await expect(page.getByRole('heading', { name: /global triggers/i })).toBeVisible()
      await settings.addTrigger(triggerName, "echo 'host trigger'")
      const card = settings.resourceCard(triggerName)
      await expect(card).toContainText('E2E trigger description')
      await expect(card).toContainText(/after|up/i)
    } finally {
      await settings.safeDeleteResource(triggerName, /delete trigger/i)
    }
  })
})
