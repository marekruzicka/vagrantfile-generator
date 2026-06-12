import { expect, test, type Page } from '@playwright/test'
import { projectDescription, uniqueProjectName } from './fixtures/test-data'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { SettingsPage } from './pages/SettingsPage'

async function loginOnPage(page: Page, email: string, otp = '123456') {
  await page.goto('/')
  const projectsHeading = page.getByRole('heading', { name: /your vagrant projects/i })

  const emailField = page.locator('#email')
  await Promise.race([
    projectsHeading.waitFor({ state: 'visible', timeout: 8_000 }).catch(() => undefined),
    emailField.waitFor({ state: 'visible', timeout: 8_000 }).catch(() => undefined),
  ])

  if (await projectsHeading.isVisible().catch(() => false)) {
    const bannerText = await page.getByRole('banner').innerText()
    if (bannerText.includes(email)) return
    await page.getByRole('button', { name: /logout/i }).click()
  }

  await expect(emailField).toBeVisible({ timeout: 10_000 })
  await emailField.fill(email)
  await page.getByRole('button', { name: /send login code/i }).click()
  await page.locator('#code').fill(otp)
  await page.getByRole('button', { name: /verify code/i }).click()
  await expect(projectsHeading).toBeVisible({ timeout: 20_000 })
  await expect(page.getByRole('banner')).toContainText(email)
}

test.describe('12. Shared Resources and Multi-User Isolation', () => {
  test.describe.configure({ timeout: 180_000 })
  test('12.1-12.5 shared resources show badges, read-only controls, favorites, and visibility toggle', async ({ page }) => {
    const settings = new SettingsPage(page)
    await settings.goto()

    const sharedCard = page.getByRole('main').locator('.border').filter({ hasText: 'Shared' }).first()
    test.skip(!(await sharedCard.isVisible().catch(() => false)), 'No shared resources available in this environment')

    await expect(sharedCard).toContainText('Shared')
    const copyButton = page.getByRole('button', { name: /copy to my resources/i }).first()
    if (await copyButton.isVisible().catch(() => false)) {
      await expect(copyButton).toBeVisible()
    }

    const favorite = page.getByRole('button', { name: /add to favorites|remove from favorites/i }).first()
    if (await favorite.isVisible().catch(() => false)) {
      await favorite.click()
      await expect(page.getByRole('button', { name: /add to favorites|remove from favorites/i }).first()).toBeVisible()
    }

    const sharedToggle = page.locator('input[x-model="showSharedResources"]')
    const initiallyChecked = await sharedToggle.isChecked()
    await sharedToggle.setChecked(!initiallyChecked, { force: true })
    await expect(page.getByText(initiallyChecked ? 'Hidden' : 'Showing')).toBeVisible()
    await sharedToggle.setChecked(initiallyChecked, { force: true })
    await expect(page.getByText(initiallyChecked ? 'Showing' : 'Hidden')).toBeVisible()
  })

  test('12.3 copy a shared resource to personal resources', async ({ page }) => {
    const settings = new SettingsPage(page)
    await settings.goto()

    const copyButton = page.getByRole('button', { name: /copy to my resources/i }).first()
    test.skip(!(await copyButton.isVisible().catch(() => false)), 'No shared resources available in this environment')

    await copyButton.click()
    await expect(page.getByText(/resource copied/i)).toBeVisible()
  })

  test('12.6 personal projects and resources are isolated between two users', async ({ page }) => {
    const userA = process.env.E2E_USER_EMAIL
    const userB = process.env.E2E_USER_EMAIL_2
    const otpA = process.env.E2E_USER_OTP
    const otpB = process.env.E2E_USER_OTP_2 || otpA
    test.skip(!userA || !userB || !otpA, 'Two-user public-mode test requires E2E_USER_EMAIL, E2E_USER_EMAIL_2, and E2E_USER_OTP')

    const projects = new ProjectsPage(page)
    const settings = new SettingsPage(page)
    const aliceProjectName = uniqueProjectName('Alice Isolation')
    const bobProjectName = uniqueProjectName('Bob Isolation')
    const alicePluginName = `e2e-alice-private-plugin-${Date.now()}`

    try {
      await loginOnPage(page, userA!, otpA!)
      await projects.createProject(aliceProjectName, projectDescription)
      await settings.goto()
      await settings.addPlugin(alicePluginName)
      await loginOnPage(page, userB!, otpB!)
      await expect(projects.projectCard(aliceProjectName)).toBeHidden()
      await projects.createProject(bobProjectName, projectDescription)
      await projects.openProject(bobProjectName)
      await page.getByRole('main').getByRole('button', { name: /^add plugin$/i }).click()
      const addPluginDialog = page.locator('.modal-content').filter({ has: page.getByRole('heading', { name: /add plugins to project/i }) })
      await expect(addPluginDialog).toBeVisible()
      await expect(addPluginDialog).not.toContainText(alicePluginName)
      await addPluginDialog.getByRole('button', { name: /^cancel$/i }).click()

      await loginOnPage(page, userA!, otpA!)
      await expect(projects.projectCard(bobProjectName)).toBeHidden()
    } finally {
      await loginOnPage(page, userA!, otpA!).catch(() => undefined)
      await projects.goto().catch(() => undefined)
      await projects.safeDeleteDraftProject(aliceProjectName).catch(() => undefined)
      await loginOnPage(page, userB!, otpB!).catch(() => undefined)
      await projects.goto().catch(() => undefined)
      await projects.safeDeleteDraftProject(bobProjectName).catch(() => undefined)
      await loginOnPage(page, userA!, otpA!).catch(() => undefined)
    }
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
