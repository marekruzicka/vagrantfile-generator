import { expect, test } from '@playwright/test'
import { projectDescription, uniqueProjectName } from './fixtures/test-data'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { SettingsPage } from './pages/SettingsPage'

test.describe('9. Project Provisioners', () => {
  test('9.1-9.3 add a provisioner to a project and include it in generated output', async ({ page }) => {
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
})
