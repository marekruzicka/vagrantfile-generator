import { expect, test } from '@playwright/test'
import { SettingsPage } from './pages/SettingsPage'

test.describe('5. Global Settings: Boxes', () => {
  test('5.1-5.4 view, create, use, and delete a user-owned box', async ({ page }) => {
    const settings = new SettingsPage(page)
    const boxName = `e2e/box-${Date.now()}`

    await settings.goto()
    try {
      await expect(page.getByRole('heading', { name: /vagrant boxes/i })).toBeVisible()
      await expect(page.getByRole('button', { name: /refresh boxes/i })).toBeVisible()
      await settings.addBox(boxName)
      const card = settings.resourceCard(boxName)
      await expect(card).toContainText('libvirt')
      await expect(card).toContainText('E2E box description')
    } finally {
      await settings.safeDeleteResource(boxName, /delete box/i)
    }
  })

  test('5.5 duplicate/invalid box validation keeps modal open', async ({ page }) => {
    const settings = new SettingsPage(page)
    await settings.goto()

    await page.getByRole('button', { name: /add box|add first box/i }).first().click()
    const dialog = page
      .getByRole('heading', { name: /add new box/i })
      .locator('xpath=ancestor::div[contains(@class, "bg-white")][1]')
    await expect(dialog).toBeVisible()
    await dialog.getByRole('button', { name: /^add box$/i }).click()
    await expect(dialog).toBeVisible()
  })
})
