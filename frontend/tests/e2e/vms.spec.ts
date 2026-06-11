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

  test('3.4 edit VM persists updated values after reload', async ({ page }) => {
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const projectName = uniqueProjectName('VM Edit')
    const originalName = `edit-${Date.now()}`
    const updatedName = `${originalName}-updated`

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.addVM({ name: originalName, labels: ['old'] })
      await detail.editVM(originalName, {
        name: updatedName,
        hostname: 'edited.local',
        memory: 2048,
        cpus: 2,
        labels: ['edited'],
        network: { type: 'private-static', ip: '192.168.56.44', netmask: '255.255.255.0' },
      })

      await page.reload()
      await expect(page.getByRole('heading', { name: /your vagrant projects/i })).toBeVisible()
      await projects.openProject(projectName)
      const card = detail.vmCard(updatedName)
      await expect(card).toContainText('edited.local')
      await expect(card).toContainText('2048 MB')
      await expect(card).toContainText('2')
      await expect(card).toContainText('edited')
      await expect(card).toContainText('192.168.56.44')
    } finally {
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
  })

  test('3.6 VM labels support quick selection, select all, and clear selection', async ({ page }) => {
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const projectName = uniqueProjectName('VM Labels')
    const baseName = `labels-${Date.now()}`

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.addVM({ name: `${baseName}-web`, labels: ['web'] })
      await detail.addVM({ name: `${baseName}-db`, labels: ['db'] })
      await detail.addVM({ name: `${baseName}-web2`, labels: ['web'] })

      await page.getByRole('button', { name: /web \(2\)/i }).click()
      await detail.expectSelectedCount(2)
      await page.getByRole('button', { name: /clear selection/i }).click()
      await expect(page.getByText('2 selected')).toBeHidden()
      await page.getByRole('button', { name: /select all/i }).click()
      await detail.expectSelectedCount(3)
    } finally {
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
  })

  test('3.7 bulk edit selected VMs leaves unselected VMs unchanged', async ({ page }) => {
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const projectName = uniqueProjectName('VM Bulk Edit')
    const baseName = `bulkedit-${Date.now()}`

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.addVM({ name: `${baseName}-a`, labels: ['bulk'] })
      await detail.addVM({ name: `${baseName}-b`, labels: ['bulk'] })
      await detail.addVM({ name: `${baseName}-c`, labels: ['control'] })

      await detail.selectVM(`${baseName}-a`)
      await detail.selectVM(`${baseName}-b`)
      await page.getByRole('button', { name: /bulk edit/i }).click()
      const dialog = page.locator('.modal-content').filter({ has: page.getByRole('heading', { name: /bulk edit vms/i }) })
      await expect(dialog).toBeVisible()
      await dialog.locator('xpath=.//label[contains(normalize-space(.), "Memory")]/following::input[1]').fill('3072')
      await dialog.locator('xpath=.//label[contains(normalize-space(.), "CPUs")]/following::input[1]').fill('3')
      await dialog.getByRole('button', { name: /^update vms$/i }).click()
      await expect(dialog).toBeHidden()

      await expect(detail.vmCard(`${baseName}-a`)).toContainText('3072 MB')
      await expect(detail.vmCard(`${baseName}-b`)).toContainText('3072 MB')
      await expect(detail.vmCard(`${baseName}-c`)).toContainText('1024 MB')
    } finally {
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
  })

  test('3.8 bulk delete removes only selected VMs', async ({ page }) => {
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const projectName = uniqueProjectName('VM Bulk Delete')
    const baseName = `bulkdelete-${Date.now()}`

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.addVM({ name: `${baseName}-a` })
      await detail.addVM({ name: `${baseName}-b` })
      await detail.addVM({ name: `${baseName}-keep` })

      await detail.selectVM(`${baseName}-a`)
      await detail.selectVM(`${baseName}-b`)
      await page.getByRole('button', { name: /bulk delete/i }).click()
      const dialog = page.locator('.modal-content').filter({ has: page.getByRole('heading', { name: /delete multiple vms/i }) })
      await expect(dialog).toBeVisible()
      await dialog.getByRole('button', { name: /delete all/i }).click()
      await expect(dialog).toBeHidden()

      await expect(detail.vmCard(`${baseName}-a`)).toBeHidden()
      await expect(detail.vmCard(`${baseName}-b`)).toBeHidden()
      await expect(detail.vmCard(`${baseName}-keep`)).toBeVisible()
      await detail.expectVMCount(1)
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
