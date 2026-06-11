import { expect, test } from '@playwright/test'
import { projectDescription, uniqueProjectName } from './fixtures/test-data'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { SettingsPage } from './pages/SettingsPage'

test.describe('9. Project Provisioners', () => {
  test('9.1 add a provisioner to a project and include it in generated output', async ({ page }) => {
    const settings = new SettingsPage(page)
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const provisionerName = `e2e-project-provisioner-${Date.now()}`
    const projectName = uniqueProjectName('Project Provisioner')

    await settings.goto()
    await settings.addProvisioner(provisionerName, 'echo project provisioner')

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.addProjectProvisioner(provisionerName)
      await detail.addVM({ name: `provisioner-vm-${Date.now()}` })

      await expect(page.getByRole('main')).toContainText(provisionerName)
      const vagrantfile = await detail.generateVagrantfile()
      await expect(vagrantfile.locator('code')).toContainText('project provisioner')
      await vagrantfile.locator('button').first().click()
    } finally {
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
      // Global provisioner cleanup is best-effort in public mode; unique names prevent collisions.
    }
  })

  test('9.2-9.3 filters, removes, and bulk-removes project provisioners', async ({ page }) => {
    const settings = new SettingsPage(page)
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const names = [0, 1, 2].map(i => `e2e-manage-provisioner-${Date.now()}-${i}`)
    const projectName = uniqueProjectName('Project Provisioner Manage')
    const card = (name: string) => page.getByRole('main').locator('.border').filter({ hasText: name }).first()

    await settings.goto()
    for (const name of names) {
      await settings.addProvisioner(name, `echo ${name}`)
    }

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      for (const name of names) {
        await detail.addProjectProvisioner(name)
      }

      await page.getByRole('main').getByRole('button', { name: /^add provisioner$/i }).click()
      const addDialog = page.locator('.modal-content').filter({ has: page.getByRole('heading', { name: /add provisioners to project/i }) })
      await expect(addDialog.locator('.flex.items-start').filter({ hasText: names[0] }).first()).toBeHidden()
      await addDialog.getByRole('button', { name: /^cancel$/i }).click()

      await card(names[1]).hover()
      await card(names[1]).locator('button:visible').last().click()
      const removeDialog = page.locator('.modal-content').filter({ has: page.getByRole('heading', { name: /remove provisioner/i }) })
      await expect(removeDialog).toBeVisible()
      await removeDialog.getByRole('button', { name: /^remove provisioner$/i }).click()
      await expect(card(names[1])).toBeHidden()

      await card(names[0]).locator('input[type="checkbox"]').check()
      await card(names[2]).locator('input[type="checkbox"]').check()
      await page.getByRole('button', { name: /bulk delete/i }).click()
      const bulkDialog = page.locator('.modal-content').filter({ has: page.getByRole('heading', { name: /bulk remove provisioners/i }) })
      await expect(bulkDialog).toBeVisible()
      await bulkDialog.getByRole('button', { name: /remove provisioners/i }).click()
      await expect(card(names[0])).toBeHidden()
      await expect(card(names[2])).toBeHidden()
    } finally {
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
  })
})
