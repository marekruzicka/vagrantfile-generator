import { expect, type Locator, type Page } from '@playwright/test'

export class SettingsPage {
  constructor(private readonly page: Page) {}

  async goto() {
    await this.page.goto('/')
    await expect(this.page.getByRole('heading', { name: /your vagrant projects/i })).toBeVisible()
    await this.page.getByRole('button', { name: /settings/i }).click()
    await expect(this.page.getByRole('heading', { name: /^settings$/i })).toBeVisible()
    await this.page.locator('#vfg-cookie-banner').getByRole('button', { name: /dismiss/i }).click().catch(() => undefined)
  }

  resourceCard(name: string): Locator {
    return this.page.getByRole('main').locator('.border').filter({ hasText: name }).first()
  }

  private modal(heading: RegExp | string): Locator {
    return this.page
      .getByRole('heading', { name: heading })
      .locator('xpath=ancestor::div[contains(@class, "bg-white") or contains(@class, "modal-content")][1]')
  }

  private fieldAfterLabel(scope: Locator, label: string): Locator {
    return scope
      .locator(`xpath=.//label[contains(normalize-space(.), "${label}")]/following::*[self::input or self::select or self::textarea][1]`)
      .first()
  }

  async addBox(name: string, description = 'E2E box description') {
    await this.page.getByRole('button', { name: /add box|add first box/i }).first().click()
    const dialog = this.modal(/add new box/i)
    await expect(dialog).toBeVisible()
    await this.fieldAfterLabel(dialog, 'Box Name').fill(name)
    await this.fieldAfterLabel(dialog, 'Description').fill(description)
    await this.fieldAfterLabel(dialog, 'Provider').selectOption('libvirt')
    await this.fieldAfterLabel(dialog, 'Version').fill('1.0.0')
    await dialog.getByRole('button', { name: /^add box$/i }).click()
    await expect(this.resourceCard(name)).toBeVisible()
  }

  async addPlugin(name: string, description = 'E2E plugin description') {
    await this.page.getByRole('button', { name: /add plugin|add first plugin/i }).first().click()
    const dialog = this.modal(/add new plugin/i)
    await expect(dialog).toBeVisible()
    await this.fieldAfterLabel(dialog, 'Plugin Name').fill(name)
    await this.fieldAfterLabel(dialog, 'Description').fill(description)
    await this.fieldAfterLabel(dialog, 'Source URL').fill('https://example.com/plugin')
    await this.fieldAfterLabel(dialog, 'Documentation URL').fill('https://example.com/plugin/docs')
    await this.fieldAfterLabel(dialog, 'Default Version').fill('1.2.3')
    await this.fieldAfterLabel(dialog, 'Plugin Configuration').fill('# E2E plugin config')
    await dialog.getByRole('button', { name: /^add plugin$/i }).click()
    await expect(this.resourceCard(name)).toBeVisible()
  }

  async addProvisioner(name: string, script = 'echo E2E provisioner') {
    await this.page.getByRole('button', { name: /add provisioner|add first provisioner/i }).first().click()
    const dialog = this.modal(/add new provisioner/i)
    await expect(dialog).toBeVisible()
    await this.fieldAfterLabel(dialog, 'Provisioner Name').fill(name)
    await this.fieldAfterLabel(dialog, 'Description').fill('E2E provisioner description')
    await this.fieldAfterLabel(dialog, 'Shell Script').fill(script)
    await dialog.locator('select').last().selectOption('always')
    await dialog.getByRole('button', { name: /^add provisioner$/i }).click()
    await expect(this.resourceCard(name)).toBeVisible()
  }

  async addTrigger(name: string, command = "echo 'E2E trigger'") {
    await this.page.getByRole('button', { name: /add trigger|add first trigger/i }).first().click()
    const dialog = this.modal(/create new trigger/i)
    await expect(dialog).toBeVisible()
    await this.fieldAfterLabel(dialog, 'Trigger Name').fill(name)
    await this.fieldAfterLabel(dialog, 'Description').fill('E2E trigger description')
    await this.fieldAfterLabel(dialog, 'Timing').selectOption('after')
    await this.fieldAfterLabel(dialog, 'Stage').selectOption('up')
    await this.fieldAfterLabel(dialog, 'Command').fill(command)
    await dialog.getByRole('button', { name: /^create trigger$/i }).click()
    await expect(this.resourceCard(name)).toBeVisible()
  }

  async safeDeleteResource(name: string, deleteButtonName: RegExp) {
    const card = this.resourceCard(name)
    if (!(await card.isVisible().catch(() => false))) return
    await card.hover()
    await card.locator('button').last().click({ timeout: 3_000 }).catch(() => undefined)
    const dialog = this.page
      .getByRole('heading', { name: deleteButtonName })
      .locator('xpath=ancestor::div[contains(@class, "bg-white") or contains(@class, "modal-content")][1]')

    if (!(await dialog.isVisible({ timeout: 3_000 }).catch(() => false))) {
      return
    }

    await expect(dialog).toContainText(name)
    await dialog.getByRole('button', { name: deleteButtonName }).click()
    await expect(card).toBeHidden()
  }
}
