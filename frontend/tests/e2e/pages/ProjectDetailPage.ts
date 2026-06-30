import { expect, type Locator, type Page } from '@playwright/test'

export class ProjectDetailPage {
  constructor(private readonly page: Page) {}

  vmCard(name: string): Locator {
    return this.page.locator('.vm-card').filter({ hasText: name }).first()
  }

  private modal(heading: RegExp | string): Locator {
    return this.page.locator('.modal-content').filter({
      has: this.page.getByRole('heading', { name: heading }),
    })
  }

  private fieldAfterLabel(scope: Locator, label: string): Locator {
    return scope
      .locator(`xpath=.//label[contains(normalize-space(.), "${label}")]/following::*[self::input or self::select or self::textarea][1]`)
      .first()
  }

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

  async addVM(options: {
    name: string
    box?: string
    hostname?: string
    memory?: number
    cpus?: number
    count?: number
    labels?: string[]
    network?:
      | { type: 'private-dhcp' }
      | { type: 'private-static'; ip: string; netmask?: string }
      | { type: 'public'; bridge?: string }
      | { type: 'forwarded-port'; host: number; guest: number; protocol?: 'TCP' | 'UDP' }
  }) {
    await this.page.getByRole('main').getByRole('button', { name: /^add vm$/i }).click()
    const dialog = this.modal(/add virtual machine/i)
    await expect(dialog).toBeVisible()

    await dialog.getByPlaceholder('vm-name').fill(options.name)
    if (options.box) {
      await this.fieldAfterLabel(dialog, 'Box').selectOption(options.box)
    }
    if (options.hostname) {
      await dialog.getByPlaceholder(/optional hostname/i).fill(options.hostname)
    }
    if (options.count) {
      await this.fieldAfterLabel(dialog, 'Count').fill(String(options.count))
    }
    if (options.memory) {
      await this.fieldAfterLabel(dialog, 'Memory').fill(String(options.memory))
    }
    if (options.cpus) {
      await this.fieldAfterLabel(dialog, 'CPUs').fill(String(options.cpus))
    }
    for (const label of options.labels || []) {
      const labelInput = dialog.getByPlaceholder(/type label and press enter/i)
      await labelInput.pressSequentially(label)
      await labelInput.press('Enter')
    }

    if (options.network) {
      await dialog.getByRole('button', { name: /add interface/i }).click()
      const iface = dialog.locator('.border.border-gray-200.rounded-lg').filter({ hasText: 'Interface 1' }).last()
      if (options.network.type === 'private-static') {
        await this.fieldAfterLabel(iface, 'IP Assignment').selectOption('static')
        await iface.getByPlaceholder('192.168.33.10').fill(options.network.ip)
        if (options.network.netmask) {
          await iface.getByPlaceholder('255.255.255.0').fill(options.network.netmask)
        }
      } else if (options.network.type === 'public') {
        await this.fieldAfterLabel(iface, 'Type').selectOption('public_network')
        if (options.network.bridge) {
          await iface.getByPlaceholder(/eth0/i).fill(options.network.bridge)
        }
      } else if (options.network.type === 'forwarded-port') {
        await this.fieldAfterLabel(iface, 'Type').selectOption('forwarded_port')
        await iface.getByPlaceholder('8080').fill(String(options.network.host))
        await iface.getByPlaceholder('80', { exact: true }).fill(String(options.network.guest))
        if (options.network.protocol) {
          await this.fieldAfterLabel(iface, 'Protocol').selectOption(options.network.protocol.toLowerCase())
        }
      }
    }

    await dialog.getByRole('button', { name: /^add vm$/i }).click()
    await expect(dialog).toBeHidden()
    await expect(this.vmCard(options.count && options.count > 1 ? `${options.name}-1` : options.name)).toBeVisible()
  }

  async expectVMVisible(name: string) {
    await expect(this.vmCard(name)).toBeVisible()
  }

  async editVM(currentName: string, options: {
    name?: string
    hostname?: string
    memory?: number
    cpus?: number
    labels?: string[]
    network?: { type: 'private-static'; ip: string; netmask?: string }
  }) {
    const card = this.vmCard(currentName)
    await expect(card).toBeVisible()
    await card.hover()
    await card.locator('button').first().click()
    const dialog = this.modal(/edit virtual machine/i)
    await expect(dialog).toBeVisible()

    if (options.name) await dialog.getByPlaceholder(/web-server/i).fill(options.name)
    if (options.hostname) await dialog.getByPlaceholder(/optional hostname/i).fill(options.hostname)
    if (options.memory) await this.fieldAfterLabel(dialog, 'Memory').fill(String(options.memory))
    if (options.cpus) await this.fieldAfterLabel(dialog, 'CPUs').fill(String(options.cpus))
    for (const label of options.labels || []) {
      const labelInput = dialog.getByPlaceholder(/type label and press enter/i)
      await labelInput.pressSequentially(label)
      await labelInput.press('Enter')
    }
    if (options.network) {
      await dialog.getByRole('button', { name: /add interface/i }).click()
      const iface = dialog.locator('.border.border-gray-200.rounded-lg').filter({ hasText: 'Interface 1' }).last()
      await this.fieldAfterLabel(iface, 'IP Assignment').selectOption('static')
      await iface.getByPlaceholder('192.168.33.10').fill(options.network.ip)
      if (options.network.netmask) {
        await iface.getByPlaceholder('255.255.255.0').fill(options.network.netmask)
      }
    }

    await dialog.getByRole('button', { name: /^update vm$/i }).click()
    await expect(dialog).toBeHidden()
    await expect(this.vmCard(options.name || currentName)).toBeVisible()
  }

  async selectVM(name: string) {
    await this.vmCard(name).locator('input[type="checkbox"]').check()
  }

  async expectSelectedCount(count: number) {
    await expect(this.page.getByText(`${count} selected`, { exact: true }).first()).toBeVisible()
  }

  async expectVMCount(count: number) {
    const main = this.page.getByRole('main')
    const vmHeading = main.getByRole('heading', {
      name: 'Virtual Machines',
      exact: true,
    })
    const projectHeader = vmHeading.locator(
      'xpath=preceding::div[contains(@class, "card")][1]'
    )
    await expect(projectHeader.getByText(`${count} VMs`).first()).toBeVisible()
  }

  async addProjectPlugin(pluginName: string) {
    await this.page.getByRole('main').getByRole('button', { name: /^add plugin$/i }).click()
    const dialog = this.modal(/add plugins to project/i)
    await expect(dialog).toBeVisible()
    await dialog.locator('.flex.items-start').filter({ hasText: pluginName }).first().click()
    await dialog.getByRole('button', { name: /^add plugin$/i }).click()
    await expect(dialog).toBeHidden()
    await expect(this.page.getByRole('main')).toContainText(pluginName)
  }

  async createPluginFromProjectAddModal(pluginName: string) {
    await this.page.getByRole('main').getByRole('button', { name: /^add plugin$/i }).click()
    const addDialog = this.modal(/add plugins to project/i)
    await expect(addDialog).toBeVisible()
    await addDialog.getByRole('button', { name: /create a new plugin configuration in settings/i }).click()

    const pluginDialog = this.page
      .getByRole('heading', { name: /add new plugin/i })
      .locator('xpath=ancestor::div[contains(@class, "bg-white") or contains(@class, "modal-content")][1]')
    await expect(pluginDialog).toBeVisible()
    await this.fieldAfterLabel(pluginDialog, 'Plugin Name').fill(pluginName)
    await this.fieldAfterLabel(pluginDialog, 'Description').fill('E2E plugin created from project')
    await this.fieldAfterLabel(pluginDialog, 'Source URL').fill('https://example.com/project-plugin')
    await this.fieldAfterLabel(pluginDialog, 'Documentation URL').fill('https://example.com/project-plugin/docs')
    await this.fieldAfterLabel(pluginDialog, 'Default Version').fill('1.2.3')
    await this.fieldAfterLabel(pluginDialog, 'Plugin Configuration').fill('# E2E project plugin config')
    await pluginDialog.getByRole('button', { name: /^add plugin$/i }).click()
    await expect(pluginDialog).toBeHidden()

    await this.addProjectPlugin(pluginName)
  }

  async addProjectProvisioner(provisionerName: string) {
    await this.page.getByRole('main').getByRole('button', { name: /^add provisioner$/i }).click()
    const dialog = this.modal(/add provisioners to project/i)
    await expect(dialog).toBeVisible()
    await dialog.locator('.flex.items-start').filter({ hasText: provisionerName }).first().click()
    await dialog.getByRole('button', { name: /^add provisioner$/i }).click()
    await expect(dialog).toBeHidden()
    await expect(this.page.getByRole('main')).toContainText(provisionerName)
  }

  async createProvisionerFromProjectAddModal(provisionerName: string, script = 'echo project-created provisioner') {
    await this.page.getByRole('main').getByRole('button', { name: /^add provisioner$/i }).click()
    const addDialog = this.modal(/add provisioners to project/i)
    await expect(addDialog).toBeVisible()
    await addDialog.getByRole('button', { name: /create a new provisioner in settings/i }).click()

    const provisionerDialog = this.page
      .getByRole('heading', { name: /add new provisioner/i })
      .locator('xpath=ancestor::div[contains(@class, "bg-white") or contains(@class, "modal-content")][1]')
    await expect(provisionerDialog).toBeVisible()
    await this.fieldAfterLabel(provisionerDialog, 'Provisioner Name').fill(provisionerName)
    await this.fieldAfterLabel(provisionerDialog, 'Description').fill('E2E provisioner created from project')
    await this.fieldAfterLabel(provisionerDialog, 'Shell Script').fill(script)
    await provisionerDialog.locator('select').first().selectOption('always')
    await provisionerDialog.getByRole('button', { name: /^add provisioner$/i }).click()
    await expect(provisionerDialog).toBeHidden()

    await this.addProjectProvisioner(provisionerName)
  }

  async addProjectTrigger(triggerName: string) {
    await this.page.getByRole('main').getByRole('button', { name: /^add trigger$/i }).click()
    const dialog = this.page
      .getByRole('heading', { name: /add triggers to project/i })
      .locator('xpath=ancestor::div[contains(@class, "bg-white")][1]')
    await expect(dialog).toBeVisible()
    await dialog.locator('.flex.items-start').filter({ hasText: triggerName }).first().click()
    await dialog.getByRole('button', { name: /add selected triggers/i }).click()
    await expect(dialog).toBeHidden()
    await expect(this.page.getByRole('main')).toContainText(triggerName)
  }

  async createTriggerFromProjectAddModal(triggerName: string, command = "echo 'project-created trigger'") {
    await this.page.getByRole('main').getByRole('button', { name: /^add trigger$/i }).click()
    const addDialog = this.page
      .getByRole('heading', { name: /add triggers to project/i })
      .locator('xpath=ancestor::div[contains(@class, "bg-white")][1]')
    await expect(addDialog).toBeVisible()
    await addDialog.getByRole('button', { name: /create a new trigger/i }).click()

    const triggerDialog = this.page
      .getByRole('heading', { name: /create new trigger/i })
      .locator('xpath=ancestor::div[contains(@class, "bg-white") or contains(@class, "modal-content")][1]')
    await expect(triggerDialog).toBeVisible()
    await this.fieldAfterLabel(triggerDialog, 'Trigger Name').fill(triggerName)
    await this.fieldAfterLabel(triggerDialog, 'Description').fill('E2E trigger created from project')
    await this.fieldAfterLabel(triggerDialog, 'Timing').selectOption('after')
    await this.fieldAfterLabel(triggerDialog, 'Stage').selectOption('up')
    await this.fieldAfterLabel(triggerDialog, 'Command').fill(command)
    await triggerDialog.getByRole('button', { name: /^create trigger$/i }).click()
    await expect(triggerDialog).toBeHidden()

    const reopenedAddDialog = this.page
      .getByRole('heading', { name: /add triggers to project/i })
      .locator('xpath=ancestor::div[contains(@class, "bg-white")][1]')
    await expect(reopenedAddDialog).toBeVisible()
    await reopenedAddDialog.locator('.flex.items-start').filter({ hasText: triggerName }).first().click()
    await reopenedAddDialog.getByRole('button', { name: /add selected triggers/i }).click()
    await expect(reopenedAddDialog).toBeHidden()
    await expect(this.page.getByRole('main')).toContainText(triggerName)
  }

  async generateVagrantfile(): Promise<Locator> {
    await this.page.getByRole('banner').getByRole('button', { name: /generate vagrantfile/i }).click()
    const dialog = this.modal(/generated vagrantfile/i)
    await expect(dialog).toBeVisible()
    return dialog
  }

  async deleteVM(name: string, confirm = true) {
    const card = this.vmCard(name)
    await expect(card).toBeVisible()
    await card.hover()
    await card.locator('button').last().click()
    const dialog = this.modal(/confirm deletion/i)
    await expect(dialog).toContainText(name)
    await dialog.getByRole('button', { name: confirm ? /^delete$/i : /^cancel$/i }).click()
    if (confirm) {
      await expect(card).toBeHidden()
    } else {
      await expect(card).toBeVisible()
    }
  }

  async backToDashboard() {
    await this.page.getByText('Vagrantfile Generator').first().click()
    await expect(
      this.page.getByRole('heading', { name: /your vagrant projects/i })
    ).toBeVisible()
  }
}
