import { expect, test } from '@playwright/test'
import { readFileSync } from 'fs'
import { projectDescription, uniqueProjectName } from './fixtures/test-data'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { SettingsPage } from './pages/SettingsPage'

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

  test('13.3-13.5 generate with plugins, provisioners, and triggers', async ({ page }) => {
    const settings = new SettingsPage(page)
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const projectName = uniqueProjectName('Generated Resources')
    const suffix = Date.now()
    const pluginName = `e2e-generated-plugin-${suffix}`
    const provisionerName = `e2e-generated-provisioner-${suffix}`
    const triggerName = `e2e-generated-trigger-${suffix}`

    await settings.goto()
    await settings.addPlugin(pluginName)
    await settings.addProvisioner(provisionerName, 'echo generated provisioner')
    await settings.addTrigger(triggerName, "echo 'generated trigger'")

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.addProjectPlugin(pluginName)
      await detail.addProjectProvisioner(provisionerName)
      await detail.addProjectTrigger(triggerName)
      await detail.addVM({ name: `generated-resources-vm-${suffix}` })

      const vagrantfile = await detail.generateVagrantfile()
      const code = vagrantfile.locator('code')
      await expect(code).toContainText(pluginName)
      await expect(code).toContainText('1.2.3')
      await expect(code).toContainText('generated provisioner')
      await expect(code).toContainText('generated trigger')
      await vagrantfile.locator('button').first().click()
    } finally {
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
  })

  test('13.6 copy generated Vagrantfile to clipboard', async ({ page, context }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write'])
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const projectName = uniqueProjectName('Copy Vagrantfile')
    const vmName = `copy-vm-${Date.now()}`

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.addVM({ name: vmName })

      const vagrantfile = await detail.generateVagrantfile()
      const displayed = await vagrantfile.locator('code').innerText()
      await vagrantfile.getByRole('button', { name: /copy to clipboard/i }).click()
      const copied = await page.evaluate(() => navigator.clipboard.readText())
      expect(copied).toBe(displayed)
      await vagrantfile.locator('button').first().click()
    } finally {
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
  })

  test('13.6 download generated Vagrantfile', async ({ page }) => {
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const projectName = uniqueProjectName('Download Vagrantfile')
    const vmName = `download-vm-${Date.now()}`

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.addVM({ name: vmName })

      const vagrantfile = await detail.generateVagrantfile()
      const [download] = await Promise.all([
        page.waitForEvent('download'),
        vagrantfile.getByRole('button', { name: /^download$/i }).click(),
      ])

      const suggestedFilename = download.suggestedFilename()
      const downloadPath = await download.path()
      expect(downloadPath).toBeTruthy()
      const content = readFileSync(downloadPath!, 'utf8')
      await vagrantfile.locator('button').first().click()

      expect(content).toContain('Vagrant.configure')
      expect(content).toContain(vmName)
      expect(suggestedFilename).toBe('Vagrantfile')
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
