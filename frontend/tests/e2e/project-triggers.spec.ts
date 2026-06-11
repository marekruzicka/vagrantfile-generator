import { expect, test } from '@playwright/test'
import { projectDescription, uniqueProjectName } from './fixtures/test-data'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { SettingsPage } from './pages/SettingsPage'

test.describe('11. Project Triggers', () => {
  test('11.1 add a trigger to a project and include it in generated output', async ({ page }) => {
    const settings = new SettingsPage(page)
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const triggerName = `e2e-project-trigger-${Date.now()}`
    const projectName = uniqueProjectName('Project Trigger')

    await settings.goto()
    await settings.addTrigger(triggerName, "echo 'project trigger'")

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.addProjectTrigger(triggerName)
      await detail.addVM({ name: `trigger-vm-${Date.now()}` })

      await expect(page.getByRole('main')).toContainText(triggerName)
      const vagrantfile = await detail.generateVagrantfile()
      await expect(vagrantfile.locator('code')).toContainText('project trigger')
      await vagrantfile.locator('button').first().click()
    } finally {
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
      // Global trigger cleanup is best-effort in public mode; unique names prevent collisions.
    }
  })

  test('11.2-11.3 searches, removes, and bulk-removes project triggers', async ({ page }) => {
    const settings = new SettingsPage(page)
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const names = [0, 1, 2].map(i => `e2e-manage-trigger-${Date.now()}-${i}`)
    const projectName = uniqueProjectName('Project Trigger Manage')
    const card = (name: string) => page.getByRole('main').locator('.border').filter({ hasText: name }).first()

    await settings.goto()
    for (const name of names) {
      await settings.addTrigger(name, `echo ${name}`)
    }

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)

      await page.getByRole('main').getByRole('button', { name: /^add trigger$/i }).click()
      const addDialog = page.getByRole('heading', { name: /add triggers to project/i }).locator('xpath=ancestor::div[contains(@class, "bg-white")][1]')
      await addDialog.getByPlaceholder(/search triggers/i).fill(names[0])
      await expect(addDialog.locator('.flex.items-start').filter({ hasText: names[0] }).first()).toBeVisible()
      await expect(addDialog.locator('.flex.items-start').filter({ hasText: names[1] }).first()).toBeHidden()
      await addDialog.getByPlaceholder(/search triggers/i).fill('')
      for (const name of names) {
        await addDialog.locator('.flex.items-start').filter({ hasText: name }).first().click()
      }
      await addDialog.getByRole('button', { name: /add selected triggers/i }).click()
      await expect(addDialog).toBeHidden()

      await card(names[1]).hover()
      await card(names[1]).locator('button:visible').last().click()
      const removeDialog = page.getByRole('heading', { name: /remove trigger/i }).locator('xpath=ancestor::div[contains(@class, "bg-white")][1]')
      await expect(removeDialog).toBeVisible()
      await removeDialog.getByRole('button', { name: /^remove trigger$/i }).click()
      await expect(card(names[1])).toBeHidden()

      await card(names[0]).locator('input[type="checkbox"]').check()
      await card(names[2]).locator('input[type="checkbox"]').check()
      await page.getByRole('button', { name: /bulk delete/i }).click()
      const bulkDialog = page.locator('.modal-content').filter({ has: page.getByRole('heading', { name: /bulk delete triggers/i }) })
      await expect(bulkDialog).toBeVisible()
      await bulkDialog.getByRole('button', { name: /remove 2 trigger/i }).click()
      await expect(card(names[0])).toBeHidden()
      await expect(card(names[2])).toBeHidden()
    } finally {
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
  })
})
