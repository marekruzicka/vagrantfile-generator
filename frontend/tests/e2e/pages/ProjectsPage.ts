import { expect, type Locator, type Page } from '@playwright/test'

export class ProjectsPage {
  constructor(private readonly page: Page) {}

  async goto() {
    await this.page.goto('/')
    await this.expectLoaded()
    await this.page.evaluate(() => {
      localStorage.setItem('vfg_cookie_banner_dismissed', '1')
      const banner = document.getElementById('vfg-cookie-banner')
      if (banner) banner.remove()
    })
  }

  async expectLoaded() {
    await expect(
      this.page.getByRole('heading', { name: /your vagrant projects/i })
    ).toBeVisible()
  }

  projectCard(name: string): Locator {
    return this.page.locator('.project-card').filter({ hasText: name }).first()
  }

  async createProject(name: string, description = '') {
    const newProject = this.page.getByRole('button', { name: /new project/i })
    const firstProject = this.page.getByRole('button', {
      name: /create your first project/i,
    })

    if (await newProject.isVisible().catch(() => false)) {
      await newProject.click()
    } else {
      await firstProject.click()
    }

    await expect(
      this.page.getByRole('heading', { name: /create new project/i })
    ).toBeVisible()
    await this.page.getByPlaceholder(/enter project name/i).fill(name)
    await this.page
      .getByPlaceholder(/optional project description/i)
      .fill(description)
    await this.page.getByRole('button', { name: /^create project$/i }).click()

    await this.expectProjectVisible(name)
  }

  async expectProjectVisible(name: string) {
    await expect(this.projectCard(name)).toBeVisible()
  }

  async expectProjectHidden(name: string) {
    await expect(this.projectCard(name)).toBeHidden()
  }

  async openProject(name: string) {
    await this.projectCard(name).click()
    await expect(this.page.getByRole('heading', { name })).toBeVisible()
  }

  async setFilter(filter: 'All' | 'Draft' | 'Ready') {
    await this.page
      .getByRole('button', { name: new RegExp(`^${filter} \\(`, 'i') })
      .click()
  }

  async deleteDraftProject(name: string, confirm = true) {
    const card = this.projectCard(name)
    await expect(card).toBeVisible()
    await card.hover()
    await card.locator('button[title="Delete project"]').click()

    const dialog = this.page.locator('.modal-content').filter({
      has: this.page.getByRole('heading', { name: /confirm deletion/i }),
    })

    await expect(dialog).toBeVisible()
    await expect(dialog).toContainText(name)

    if (confirm) {
      await dialog.getByRole('button', { name: /^delete$/i }).click()
      await this.expectProjectHidden(name)
    } else {
      await dialog.getByRole('button', { name: /^cancel$/i }).click()
      await this.expectProjectVisible(name)
    }
  }

  async safeDeleteDraftProject(name: string) {
    if (await this.projectCard(name).isVisible().catch(() => false)) {
      await this.deleteDraftProject(name, true)
    }
  }
}
