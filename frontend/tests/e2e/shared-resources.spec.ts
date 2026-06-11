import { expect, test } from '@playwright/test'
import { projectDescription, uniqueProjectName } from './fixtures/test-data'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { SettingsPage } from './pages/SettingsPage'

test.describe('12. Shared Resources and Multi-User Isolation', () => {
  test('12.1-12.5 shared resources show badges, read-only controls, favorites, and visibility toggle', async ({ page }) => {
    const settings = new SettingsPage(page)
    await settings.goto()

    const sharedCard = page.getByRole('main').locator('.border').filter({ hasText: 'Shared' }).first()
    test.skip(!(await sharedCard.isVisible().catch(() => false)), 'No shared resources available in this environment')

    await expect(sharedCard).toContainText('Shared')
    await expect(sharedCard.getByRole('button', { name: /copy to my resources/i })).toBeVisible()

    const favorite = page.getByRole('button', { name: /add to favorites|remove from favorites/i }).first()
    await favorite.click()
    await expect(page.getByRole('button', { name: /add to favorites|remove from favorites/i }).first()).toBeVisible()

    await page.getByRole('checkbox', { name: /showing/i }).click({ force: true })
    await expect(page.getByText('Hidden')).toBeVisible()
    await page.getByRole('checkbox', { name: /hidden/i }).click({ force: true })
    await expect(page.getByText('Showing')).toBeVisible()
  })

  test('12.3 copy a shared resource to personal resources', async ({ page }) => {
    const settings = new SettingsPage(page)
    await settings.goto()

    const copyButton = page.getByRole('button', { name: /copy to my resources/i }).first()
    test.skip(!(await copyButton.isVisible().catch(() => false)), 'No shared resources available in this environment')

    await copyButton.click()
    await expect(page.getByText(/resource copied/i)).toBeVisible()
  })

  test('12.7 shared box can be used in a personal project without modifying original', async ({ page }) => {
    const settings = new SettingsPage(page)
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const projectName = uniqueProjectName('Shared Box Usage')

    await settings.goto()
    const sharedCard = page.getByRole('main').locator('.border').filter({ hasText: 'Shared' }).first()
    test.skip(!(await sharedCard.isVisible().catch(() => false)), 'No shared resources available in this environment')
    const sharedBoxName = (await sharedCard.getByRole('heading').first().innerText()).trim()

    await projects.goto()
    try {
      await projects.createProject(projectName, projectDescription)
      await projects.openProject(projectName)
      await detail.addVM({ name: `shared-box-vm-${Date.now()}`, box: sharedBoxName })
      const vagrantfile = await detail.generateVagrantfile()
      await expect(vagrantfile.locator('code')).toContainText(sharedBoxName)
      await vagrantfile.locator('button').first().click()
    } finally {
      await detail.backToDashboard().catch(() => undefined)
      await projects.safeDeleteDraftProject(projectName)
    }
  })
})
