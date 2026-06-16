import { expect, test, type Locator, type Page } from '@playwright/test'
import { mkdirSync } from 'node:fs'

const authFile = '.auth/user.json'

type EntryState = 'login' | 'projects'

async function waitForEntryState(
  page: Page,
  projectsHeading: Locator,
  emailField: Locator
): Promise<EntryState> {
  const deadline = Date.now() + 20_000

  while (Date.now() < deadline) {
    if (await projectsHeading.isVisible().catch(() => false)) {
      return 'projects'
    }

    if (await emailField.isVisible().catch(() => false)) {
      return 'login'
    }

    await page.waitForTimeout(250)
  }

  throw new Error(
    `Timed out waiting for either the Projects page or Login page. Current URL: ${page.url()}`
  )
}

test('authenticate for E2E tests or capture self-hosted session', async ({ page }) => {
  mkdirSync('.auth', { recursive: true })

  await page.goto('/')

  const projectsHeading = page.getByRole('heading', {
    name: /your vagrant projects/i,
  })
  const emailField = page.getByLabel(/email address/i)

  const entryState = await waitForEntryState(page, projectsHeading, emailField)

  if (entryState === 'login') {
    const email = process.env.TEST_USER_EMAIL_1
    const otp = process.env.TEST_USER_OTP_1

    if (!email || !otp) {
      throw new Error(
        'Public-mode login detected. Set TEST_USER_EMAIL_1 and TEST_USER_OTP_1 before running E2E tests.'
      )
    }

    await emailField.fill(email)
    await page.getByRole('button', { name: /send login code/i }).click()
    await page.getByLabel(/enter 6-digit code/i).fill(otp)
    await page.getByRole('button', { name: /verify code/i }).click()
  }

  await expect(projectsHeading).toBeVisible({ timeout: 20_000 })
  await page.context().storageState({ path: authFile })
})
