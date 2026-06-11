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

      await card.hover()
      await card.locator('button:visible').first().click()
      const editDialog = page
        .getByRole('heading', { name: /edit trigger/i })
        .locator('xpath=ancestor::div[contains(@class, "bg-white")][1]')
      await expect(editDialog).toBeVisible()
      await editDialog.locator('xpath=.//label[contains(normalize-space(.), "Description")]/following::textarea[1]').fill('Updated E2E trigger description')
      await editDialog.locator('xpath=.//label[contains(normalize-space(.), "Command")]/following::textarea[1]').fill("echo 'updated trigger'")
      await editDialog.getByRole('button', { name: /^update trigger$/i }).click()
      await expect(editDialog).toBeHidden()
      await expect(settings.resourceCard(triggerName)).toContainText('Updated E2E trigger description')
    } finally {
      await settings.safeDeleteResource(triggerName, /delete trigger/i)
    }
  })

  test('10.3 create a remote trigger and validate hidden command handling', async ({ page }) => {
    const settings = new SettingsPage(page)
    const triggerName = `e2e-remote-trigger-${Date.now()}`

    await settings.goto()
    try {
      await page.getByRole('button', { name: /add trigger|add first trigger/i }).first().click()
      const dialog = page
        .getByRole('heading', { name: /create new trigger/i })
        .locator('xpath=ancestor::div[contains(@class, "bg-white")][1]')
      await expect(dialog).toBeVisible()
      await dialog.locator('xpath=.//label[contains(normalize-space(.), "Trigger Name")]/following::input[1]').fill(triggerName)
      await dialog.locator('xpath=.//label[contains(normalize-space(.), "Description")]/following::textarea[1]').fill('Remote E2E trigger description')
      await dialog.getByLabel(/run remotely/i).check()
      await dialog.locator('textarea[placeholder*="sudo systemctl"]').fill('echo remote trigger')
      await dialog.getByRole('button', { name: /^create trigger$/i }).click()
      await expect(dialog).toBeHidden()
      await expect(settings.resourceCard(triggerName)).toContainText('Remote E2E trigger description')
    } finally {
      await settings.safeDeleteResource(triggerName, /delete trigger/i)
    }
  })
})
