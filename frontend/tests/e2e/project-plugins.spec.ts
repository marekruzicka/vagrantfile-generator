import { expect, test } from '@playwright/test'
import { projectDescription, uniqueProjectName } from './fixtures/test-data'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { SettingsPage } from './pages/SettingsPage'

test.describe('7. Project Plugins', () => {
  test.describe.configure({ timeout: 180_000 })
  test('7.1-7.4 add a global plugin to a project and generated Vagrantfile', async ({ page }) => {
    const settings = new SettingsPage(page)
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const pluginName = `e2e-project-plugin-${Date.now()}`
    const projectName = uniqueProjectName('Project Plugin')

    await settings.goto()
    await settings.addPlugin(pluginName)

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.addProjectPlugin(pluginName)
      await detail.addVM({ name: `plugin-vm-${Date.now()}` })

      await expect(page.getByRole('main')).toContainText(pluginName)
      const vagrantfile = await detail.generateVagrantfile()
      await expect(vagrantfile.locator('code')).toContainText(pluginName)
      await vagrantfile.locator('button').first().click()
    } finally {
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
      // Global plugin cleanup is intentionally skipped here because public-mode
      // shared-resource ownership can make delete controls unavailable. Unique
      // E2E names prevent later runs from colliding.
    }
  })

  test('7.2 add-plugin modal filters already assigned plugins', async ({ page }) => {
    const settings = new SettingsPage(page)
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const pluginName = `e2e-filter-plugin-${Date.now()}`
    const projectName = uniqueProjectName('Project Plugin Filter')

    await settings.goto()
    await settings.addPlugin(pluginName)

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.addProjectPlugin(pluginName)
      await page.getByRole('main').getByRole('button', { name: /^add plugin$/i }).click()
      const dialog = page.locator('.modal-content').filter({ has: page.getByRole('heading', { name: /add plugins to project/i }) })
      await expect(dialog).toBeVisible()
      await expect(
        dialog.locator('.flex.items-start').filter({ hasText: pluginName }).first()
      ).toBeHidden()
    } finally {
      await page.locator('.modal-content').filter({ has: page.getByRole('heading', { name: /add plugins to project/i }) }).getByRole('button', { name: /^cancel$/i }).click().catch(() => undefined)
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
      // Global plugin cleanup is intentionally skipped here because public-mode
      // shared-resource ownership can make delete controls unavailable. Unique
      // E2E names prevent later runs from colliding.
    }
  })
})
