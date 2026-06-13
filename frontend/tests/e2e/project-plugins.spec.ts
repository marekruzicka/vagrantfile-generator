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

  test('7.6 creates a plugin from the project add-plugin flow', async ({ page }) => {
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const pluginName = `e2e-project-created-plugin-${Date.now()}`
    const projectName = uniqueProjectName('Project Plugin Create')

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.createPluginFromProjectAddModal(pluginName)
      await expect(page.getByRole('main')).toContainText(pluginName)
    } finally {
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
  })

  test('7.3-7.5 edit, remove, and bulk remove project plugins', async ({ page }) => {
    const settings = new SettingsPage(page)
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const projectName = uniqueProjectName('Project Plugin Manage')
    const plugins = [0, 1, 2].map(i => `e2e-manage-plugin-${Date.now()}-${i}`)
    const projectPluginCard = (name: string) => page.getByRole('main').locator('.border').filter({ hasText: name }).first()

    await settings.goto()
    for (const plugin of plugins) {
      await settings.addPlugin(plugin)
    }

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      for (const plugin of plugins) {
        await detail.addProjectPlugin(plugin)
      }
      await detail.addVM({ name: `plugin-manage-vm-${Date.now()}` })

      await projectPluginCard(plugins[0]).hover()
      await projectPluginCard(plugins[0]).locator('button:visible').first().click()
      const editDialog = page.getByRole('heading', { name: /edit plugin/i }).locator('xpath=ancestor::div[contains(@class, "bg-white")][1]')
      await expect(editDialog).toBeVisible()
      await editDialog.locator('xpath=.//label[contains(normalize-space(.), "Default Version")]/following::input[1]').fill('2.3.4')
      await editDialog.getByRole('button', { name: /^update plugin$/i }).click()
      await expect(editDialog).toBeHidden()
      const vagrantfile = await detail.generateVagrantfile()
      await expect(vagrantfile.locator('code')).toContainText('2.3.4')
      await vagrantfile.locator('button').first().click()

      await projectPluginCard(plugins[1]).hover()
      await projectPluginCard(plugins[1]).locator('button:visible').last().click()
      const removeDialog = page.locator('.modal-content').filter({ has: page.getByRole('heading', { name: /^remove plugin$/i }) })
      await expect(removeDialog).toBeVisible()
      await removeDialog.getByRole('button', { name: /^remove plugin$/i }).click()
      await expect(projectPluginCard(plugins[1])).toBeHidden()

      await projectPluginCard(plugins[0]).locator('input[type="checkbox"]').check()
      await projectPluginCard(plugins[2]).locator('input[type="checkbox"]').check()
      await page.getByRole('button', { name: /bulk delete/i }).click()
      const bulkDialog = page.locator('.modal-content').filter({ has: page.getByRole('heading', { name: /bulk delete plugins/i }) })
      await expect(bulkDialog).toBeVisible()
      await bulkDialog.getByRole('button', { name: /remove 2 plugins/i }).click()
      await expect(projectPluginCard(plugins[0])).toBeHidden()
      await expect(projectPluginCard(plugins[2])).toBeHidden()
    } finally {
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
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
