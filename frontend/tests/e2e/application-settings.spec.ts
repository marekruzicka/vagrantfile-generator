import { expect, test } from '@playwright/test'
import { projectDescription, uniqueProjectName } from './fixtures/test-data'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { ProjectsPage } from './pages/ProjectsPage'
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

  test('14.1 VM limits affect VM form validation', async ({ page }) => {
    const settings = new SettingsPage(page)
    const projects = new ProjectsPage(page)
    const projectName = uniqueProjectName('Settings Limits')

    await settings.goto()
    const maxCpuInput = page.locator('xpath=.//label[contains(normalize-space(.), "Maximum CPUs")]/following::input[1]')
    const originalMaxCpu = await maxCpuInput.inputValue()
    await maxCpuInput.fill('2')
    await page.getByRole('button', { name: /save vm limits/i }).click()

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await page.getByRole('main').getByRole('button', { name: /^add vm$/i }).click()
      const dialog = page.locator('.modal-content').filter({ has: page.getByRole('heading', { name: /add virtual machine/i }) })
      await dialog.getByPlaceholder('vm-name').fill(`limit-vm-${Date.now()}`)
      const cpuInput = dialog.locator('xpath=.//label[contains(normalize-space(.), "CPUs")]/following::input[1]')
      await expect(cpuInput).toHaveAttribute('max', '2')
      await cpuInput.fill('3')
      await dialog.getByRole('button', { name: /^add vm$/i }).click()
      await expect(dialog).toContainText(/please correct/i)
      await page.keyboard.press('Escape')
    } finally {
      await page.evaluate(value => {
        const key = 'vagrantfile-generator-config'
        const current = JSON.parse(localStorage.getItem(key) || '{}')
        localStorage.setItem(key, JSON.stringify({ ...current, maxCpus: Number(value) }))
      }, originalMaxCpu).catch(() => undefined)
      await projects.goto().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
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

  test('14.2 Project Detail sections collapse and expand', async ({ page }) => {
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const projectName = uniqueProjectName('Detail Collapse')

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.addVM({ name: `collapse-vm-${Date.now()}` })

      await page.getByRole('heading', { name: 'Virtual Machines', exact: true }).click()
      await expect(page.getByRole('main').getByRole('button', { name: /^add vm$/i })).toBeHidden()
      await page.getByRole('heading', { name: 'Virtual Machines', exact: true }).click()
      await expect(page.getByRole('main').getByRole('button', { name: /^add vm$/i })).toBeVisible()
    } finally {
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
  })
})
