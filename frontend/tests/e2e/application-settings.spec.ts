import { expect, test } from '@playwright/test'
import { SettingsPage } from './pages/SettingsPage'

test.describe('14. Global Application Settings', () => {
  test('14.1 network and VM limit settings persist after save/reload', async ({ page }) => {
    const settings = new SettingsPage(page)
    await settings.goto()

    const publicIpCheckbox = page.locator('#allowPublicIPs')
    const initiallyChecked = await publicIpCheckbox.isChecked()
    await publicIpCheckbox.setChecked(!initiallyChecked, { force: true })

    await page.locator('xpath=.//label[contains(normalize-space(.), "Maximum CPUs")]/following::input[1]').fill('6')
    await page.locator('xpath=.//label[contains(normalize-space(.), "Maximum Memory")]/following::input[1]').fill('12288')
    await page.locator('xpath=.//label[contains(normalize-space(.), "Minimum Memory")]/following::input[1]').fill('512')
    await page.locator('xpath=.//label[contains(normalize-space(.), "Memory Step")]/following::input[1]').fill('256')
    await page.getByRole('button', { name: /save vm limits/i }).click()

    await page.reload()
    await expect(page.getByRole('heading', { name: /your vagrant projects/i })).toBeVisible()
    await page.getByRole('button', { name: /settings/i }).click()
    await expect(page.getByRole('heading', { name: /^settings$/i })).toBeVisible()
    await expect(page.locator('xpath=.//label[contains(normalize-space(.), "Maximum CPUs")]/following::input[1]')).toHaveValue('6')
    await expect(publicIpCheckbox).toBeChecked({ checked: !initiallyChecked })

    // Restore public-IP setting to its original state for later tests/users.
    await publicIpCheckbox.setChecked(initiallyChecked, { force: true })
  })

  test('14.2-14.3 collapsible sections and refresh controls remain usable', async ({ page }) => {
    const settings = new SettingsPage(page)
    await settings.goto()

    await expect(page.getByRole('heading', { name: /vagrant boxes/i })).toBeVisible()
    await page.getByRole('button', { name: /refresh boxes/i }).click()
    await expect(page.getByRole('button', { name: /add box/i })).toBeVisible()

    await page.getByRole('heading', { name: /vagrant boxes/i }).click()
    await expect(page.getByRole('button', { name: /add box/i })).toBeHidden()
    await page.getByRole('heading', { name: /vagrant boxes/i }).click()
    await expect(page.getByRole('button', { name: /add box/i })).toBeVisible()
  })
})
