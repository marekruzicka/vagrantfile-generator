import { expect, test } from '@playwright/test'
import { projectDescription, uniqueProjectName } from './fixtures/test-data'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { ProjectsPage } from './pages/ProjectsPage'

test.describe('4. Networking', () => {
  test.describe.configure({ timeout: 120_000 })
  test('4.1-4.4 VM networking options appear on cards and generated Vagrantfile', async ({ page }) => {
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const projectName = uniqueProjectName('Networking')

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)

      await detail.addVM({ name: `dhcp-${Date.now()}`, network: { type: 'private-dhcp' } })
      await detail.addVM({
        name: `static-${Date.now()}`,
        network: { type: 'private-static', ip: '192.168.56.20', netmask: '255.255.255.0' },
      })
      await detail.addVM({
        name: `public-${Date.now()}`,
        network: { type: 'public', bridge: 'eth0' },
      })
      await detail.addVM({
        name: `port-${Date.now()}`,
        network: { type: 'forwarded-port', host: 18080, guest: 80, protocol: 'TCP' },
      })

      await expect(page.getByRole('main')).toContainText('Private Network')
      await expect(page.getByRole('main')).toContainText('192.168.56.20')
      await expect(page.getByRole('main')).toContainText('Public Network')
      await expect(page.getByRole('main')).toContainText('Port Forwarding')

      const vagrantfile = await detail.generateVagrantfile()
      await expect(vagrantfile.locator('code')).toContainText('private_network')
      await expect(vagrantfile.locator('code')).toContainText('192.168.56.20')
      await expect(vagrantfile.locator('code')).toContainText('public_network')
      await expect(vagrantfile.locator('code')).toContainText('forwarded_port')
      await expect(vagrantfile.locator('code')).toContainText('18080')
      await vagrantfile.locator('button').first().click()
      await expect(vagrantfile).toBeHidden()
    } finally {
      await page.keyboard.press('Escape').catch(() => undefined)
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
  })

  test('4.5 bulk static IPs increment for bulk-created VMs', async ({ page }) => {
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const projectName = uniqueProjectName('Networking Bulk IP')
    const baseName = `ipbulk-${Date.now()}`

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.addVM({
        name: baseName,
        count: 2,
        network: { type: 'private-static', ip: '192.168.57.30' },
      })

      const vagrantfile = await detail.generateVagrantfile()
      await expect(vagrantfile.locator('code')).toContainText('192.168.57.30')
      await expect(vagrantfile.locator('code')).toContainText('192.168.57.31')
      await vagrantfile.locator('button').first().click()
      await expect(vagrantfile).toBeHidden()
    } finally {
      await page.keyboard.press('Escape').catch(() => undefined)
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
  })
})
