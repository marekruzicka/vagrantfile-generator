import { expect, test } from '@playwright/test'
import { projectDescription, uniqueProjectName } from './fixtures/test-data'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { ProjectsPage } from './pages/ProjectsPage'

test.describe('3. Virtual Machines', () => {
  test('3.1 add a single VM displays configuration and updates count', async ({ page }) => {
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const projectName = uniqueProjectName('VM Add')
    const vmName = `web-${Date.now()}`

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.addVM({
        name: vmName,
        hostname: `${vmName}.local`,
        memory: 1536,
        cpus: 2,
        labels: ['web'],
      })

      const card = detail.vmCard(vmName)
      await expect(card).toContainText('generic/debian12')
      await expect(card).toContainText('1536 MB')
      await expect(card).toContainText('2')
      await expect(card).toContainText(`${vmName}.local`)
      await expect(card).toContainText('web')
      await detail.expectVMCount(1)
    } finally {
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
  })

  test('3.2 validates required VM fields and resource limits', async ({ page }) => {
    const projects = new ProjectsPage(page)
    const projectName = uniqueProjectName('VM Validation')

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await page.getByRole('main').getByRole('button', { name: /^add vm$/i }).click()
      const dialog = page.locator('.modal-content').filter({
        has: page.getByRole('heading', { name: /add virtual machine/i }),
      })
      await dialog.getByPlaceholder('vm-name').fill('bad name!')
      await dialog
        .locator('xpath=.//label[contains(normalize-space(.), "Memory")]/following::input[1]')
        .fill('1')
      await dialog
        .locator('xpath=.//label[contains(normalize-space(.), "CPUs")]/following::input[1]')
        .fill('0')
      await dialog.getByRole('button', { name: /^add vm$/i }).click()

      await expect(dialog).toBeVisible()
      await expect(dialog).toContainText(/Please correct the following errors/i)
    } finally {
      await page.keyboard.press('Escape').catch(() => undefined)
      await projects.goto().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
  })

  test('3.3 bulk create VMs uses suffixed names', async ({ page }) => {
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const projectName = uniqueProjectName('VM Bulk')
    const baseName = `bulk-${Date.now()}`

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.addVM({ name: baseName, count: 3, labels: ['batch'] })

      await detail.expectVMVisible(`${baseName}-1`)
      await detail.expectVMVisible(`${baseName}-2`)
      await detail.expectVMVisible(`${baseName}-3`)
      await detail.expectVMCount(3)
    } finally {
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
  })

  test('3.5 delete VM supports cancel and confirm', async ({ page }) => {
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const projectName = uniqueProjectName('VM Delete')
    const vmName = `delete-${Date.now()}`

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.addVM({ name: vmName })

      await detail.deleteVM(vmName, false)
      await detail.deleteVM(vmName, true)
      await detail.expectVMCount(0)
    } finally {
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
  })
})
