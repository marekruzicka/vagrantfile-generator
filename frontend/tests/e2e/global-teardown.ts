import { request, type APIRequestContext } from '@playwright/test'
import { existsSync } from 'node:fs'

const baseURL = process.env.E2E_BASE_URL || 'http://localhost:8080'
const authFile = '.auth/user.json'
const e2eNamePattern = /^e2e-/i

type ResourceSummary = {
  id: string
  name: string
}

type ResourceKind = 'plugins' | 'provisioners' | 'triggers' | 'boxes' | 'projects'

async function cleanupResourceKind(api: APIRequestContext, kind: ResourceKind): Promise<void> {
  const listResponse = await api.get(`/api/${kind}`)

  if (!listResponse.ok()) {
    console.warn(
      `[e2e cleanup] Could not list ${kind}: ${listResponse.status()} ${await listResponse.text()}`
    )
    return
  }

  const resources = (await listResponse.json()) as ResourceSummary[]
  const e2eResources = resources.filter(resource => e2eNamePattern.test(resource.name))

  for (const resource of e2eResources) {
    const deleteResponse = await api.delete(`/api/${kind}/${resource.id}`)

    if (deleteResponse.ok() || deleteResponse.status() === 404) {
      console.log(`[e2e cleanup] Deleted ${kind.slice(0, -1)}: ${resource.name}`)
      continue
    }

    // In public mode, shared resources are intentionally read-only. They can be
    // visible in lists, but the API correctly refuses to delete them.
    if (deleteResponse.status() === 403) {
      console.warn(`[e2e cleanup] Skipped read-only ${kind.slice(0, -1)}: ${resource.name}`)
      continue
    }

    console.warn(
      `[e2e cleanup] Could not delete ${kind.slice(0, -1)} ${resource.name}: ` +
        `${deleteResponse.status()} ${await deleteResponse.text()}`
    )
  }
}

export default async function globalTeardown(): Promise<void> {
  if (process.env.E2E_CLEANUP === '0') {
    console.log('[e2e cleanup] Skipped because E2E_CLEANUP=0')
    return
  }

  const api = await request.newContext({
    baseURL,
    ...(existsSync(authFile) ? { storageState: authFile } : {}),
  })

  try {
    for (const kind of ['plugins', 'provisioners', 'triggers'] as const) {
      await cleanupResourceKind(api, kind)
    }
  } finally {
    await api.dispose()
  }
}
