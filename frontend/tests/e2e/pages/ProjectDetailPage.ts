import { expect, type Page } from '@playwright/test'

export class ProjectDetailPage {
  constructor(private readonly page: Page) {}

  async expectLoaded(name: string, description?: string) {
    const main = this.page.getByRole('main')
    const projectHeading = main.getByRole('heading', { name })
    const projectHeader = projectHeading.locator(
      'xpath=ancestor::div[contains(@class, "card")][1]'
    )

    await expect(projectHeading).toBeVisible()
    if (description) {
      await expect(projectHeader).toContainText(description)
    }
    await expect(projectHeader.getByText(/0 VMs/).first()).toBeVisible()
    await expect(projectHeader.getByText(/^draft$|^ready$/i).first()).toBeVisible()
    await expect(main.getByRole('heading', { name: 'Plugins' })).toBeVisible()
    await expect(
      main.getByRole('heading', { name: 'Provisioners' })
    ).toBeVisible()
    await expect(main.getByRole('heading', { name: 'Triggers' })).toBeVisible()
    await expect(
      main.getByRole('heading', { name: 'Virtual Machines', exact: true })
    ).toBeVisible()
  }

  async changeStatus(status: 'Draft' | 'Ready') {
    await this.page.getByRole('button', { name: /change status/i }).click()
    await this.page.getByRole('button', { name: status }).click()
    await expect(
      this.page.getByText(new RegExp(`Project deployment status updated to ${status.toLowerCase()}`, 'i'))
    ).toBeVisible()
  }

  async expectReadyLocked() {
    await expect(this.page.getByText(/project locked - read only/i)).toBeVisible()
    await expect(
      this.page.getByRole('banner').getByRole('button', { name: /^add vm$/i })
    ).toBeHidden()
  }

  async expectDraftEditable() {
    await expect(this.page.getByText(/project locked - read only/i)).toBeHidden()
    await expect(
      this.page.getByRole('banner').getByRole('button', { name: /^add vm$/i })
    ).toBeVisible()
  }

  async backToDashboard() {
    await this.page.getByText('Vagrantfile Generator').first().click()
    await expect(
      this.page.getByRole('heading', { name: /your vagrant projects/i })
    ).toBeVisible()
  }
}
