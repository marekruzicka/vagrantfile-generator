import { expect, test } from '@playwright/test'
import { projectDescription, uniqueProjectName } from './fixtures/test-data'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { SettingsPage } from './pages/SettingsPage'

test.describe('11. Project Triggers', () => {
  test('11.1-11.3 add a trigger to a project and include it in generated output', async ({ page }) => {
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
})
