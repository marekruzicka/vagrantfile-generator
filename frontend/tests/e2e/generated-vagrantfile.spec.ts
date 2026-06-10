import { expect, test } from '@playwright/test'
import { projectDescription, uniqueProjectName } from './fixtures/test-data'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { ProjectsPage } from './pages/ProjectsPage'

test.describe('13. Generated Vagrantfile', () => {
  test('13.1-13.2 generate simple and multi-VM Vagrantfile content', async ({ page }) => {
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const projectName = uniqueProjectName('Generated Vagrantfile')

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.addVM({ name: `app-${Date.now()}`, hostname: 'app.local', memory: 2048, cpus: 2 })
      await detail.addVM({ name: `db-${Date.now()}` })

      const vagrantfile = await detail.generateVagrantfile()
      const code = vagrantfile.locator('code')
      await expect(code).toContainText('Vagrant.configure')
      await expect(code).toContainText('generic/debian12')
      await expect(code).toContainText('app.local')
      await expect(code).toContainText('memory = 2048')
      await expect(code).toContainText('cpus = 2')
      await expect(code).toContainText('# VM: db-')
      await vagrantfile.locator('button').first().click()
    } finally {
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
  })

  test('13.7 generation action is unavailable for a project with no VMs', async ({ page }) => {
    const projects = new ProjectsPage(page)
    const projectName = uniqueProjectName('Generated Empty')

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await expect(
        page.getByRole('banner').getByRole('button', { name: /generate vagrantfile/i })
      ).toBeHidden()
    } finally {
      await projects.goto().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
  })
})
