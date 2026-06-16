import { expect, test } from '@playwright/test'
import { projectDescription, uniqueProjectName } from './fixtures/test-data'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { ProjectsPage } from './pages/ProjectsPage'

test.describe('2. Projects Dashboard', () => {
  test('2.1 empty first-run experience is helpful when no projects exist', async ({
    page,
  }) => {
    const projects = new ProjectsPage(page)
    await projects.goto()

    const emptyState = page.getByRole('heading', {
      name: /ready to start building/i,
    })
    test.skip(
      !(await emptyState.isVisible().catch(() => false)),
      'Environment already contains projects; empty first-run state is not applicable.'
    )

    const main = page.getByRole('main')

    await expect(emptyState).toBeVisible()
    await expect(main.getByText(/create your first vagrant project/i)).toBeVisible()
    await expect(main.getByRole('heading', { name: 'Create Project' })).toBeVisible()
    await expect(main.getByRole('heading', { name: 'Add VMs' })).toBeVisible()
    await expect(main.getByRole('heading', { name: 'Generate & Use' })).toBeVisible()
    await expect(
      main.getByRole('button', { name: /create your first project/i })
    ).toBeVisible()
  })

  test('2.2 create project: project appears as Draft with correct card stats', async ({
    page,
  }) => {
    const projects = new ProjectsPage(page)
    const name = uniqueProjectName('Create Project')

    await projects.goto()
    try {
      await projects.createProject(name, projectDescription)
      const card = projects.projectCard(name)
      await expect(card).toContainText(projectDescription)
      await expect(card).toContainText('0 VMs')
      await expect(card).toContainText('Draft')
    } finally {
      await projects.safeDeleteDraftProject(name)
    }
  })

  test('2.3 project list stats and filters distinguish Draft and Ready projects', async ({
    page,
  }) => {
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const draftName = uniqueProjectName('Draft Filter')
    const readyName = uniqueProjectName('Ready Filter')

    await projects.goto()
    try {
      await projects.createProject(draftName, projectDescription)
      await projects.createProject(readyName, projectDescription)

      await projects.openProject(readyName)
      await detail.changeStatus('Ready')
      await detail.backToDashboard()

      await expect(page.getByRole('button', { name: /^all \(/i })).toBeVisible()
      await expect(page.getByRole('button', { name: /^draft \(/i })).toBeVisible()
      await expect(page.getByRole('button', { name: /^ready \(/i })).toBeVisible()

      await projects.setFilter('Draft')
      await projects.expectProjectVisible(draftName)
      await projects.expectProjectHidden(readyName)

      await projects.setFilter('Ready')
      await projects.expectProjectVisible(readyName)
      await projects.expectProjectHidden(draftName)

      await projects.setFilter('All')
      await projects.expectProjectVisible(draftName)
      await projects.expectProjectVisible(readyName)
    } finally {
      await projects.setFilter('All').catch(() => undefined)
      if (await projects.projectCard(readyName).isVisible().catch(() => false)) {
        await projects.openProject(readyName)
        await detail.changeStatus('Draft').catch(() => undefined)
        await detail.backToDashboard()
      }
      await projects.safeDeleteDraftProject(draftName)
      await projects.safeDeleteDraftProject(readyName)
    }
  })

  test('2.4 open project detail shows dashboard project metadata and sections', async ({
    page,
  }) => {
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const name = uniqueProjectName('Open Detail')

    await projects.goto()
    try {
      await projects.createProject(name, projectDescription)
      await projects.openProject(name)
      await detail.expectLoaded(name, projectDescription)
      await detail.backToDashboard()
    } finally {
      await projects.safeDeleteDraftProject(name)
    }
  })

  test('2.5 delete draft project supports cancel and confirm flows', async ({
    page,
  }) => {
    const projects = new ProjectsPage(page)
    const name = uniqueProjectName('Delete Draft')

    await projects.goto()
    await projects.createProject(name, projectDescription)
    await projects.deleteDraftProject(name, false)
    await projects.deleteDraftProject(name, true)
  })

  test('2.6 ready project protection locks editing/destructive actions and draft restore unlocks them', async ({
    page,
  }) => {
    const projects = new ProjectsPage(page)
    const detail = new ProjectDetailPage(page)
    const name = uniqueProjectName('Ready Protection')

    await projects.goto()
    try {
      await projects.createProject(name, projectDescription)
      await projects.openProject(name)
      await detail.changeStatus('Ready')
      await detail.expectReadyLocked()
      await detail.backToDashboard()

      const readyCard = projects.projectCard(name)
      await expect(readyCard).toContainText('Ready')
      await expect(
        readyCard.locator('button[title="Cannot delete locked project"]')
      ).toBeDisabled()

      await projects.openProject(name)
      await detail.changeStatus('Draft')
      await detail.expectDraftEditable()
      await detail.backToDashboard()
      await expect(projects.projectCard(name)).toContainText('Draft')
    } finally {
      await projects.safeDeleteDraftProject(name)
    }
  })
})
