import { request, type APIRequestContext } from '@playwright/test'
import { existsSync, readFileSync } from 'node:fs'

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const baseURL = process.env.E2E_BASE_URL || 'http://localhost:8080'
const authFile = '.auth/user.json'

// ---------------------------------------------------------------------------
// Naming conventions used by E2E tests (see test-data.ts and spec files)
// ---------------------------------------------------------------------------
const E2E_PROJECT_PREFIX = /^E2E /i
const E2E_BOX_PREFIX = /^e2e[/-]/i
const E2E_RESOURCE_PREFIX = /^e2e-/i

// ---------------------------------------------------------------------------
// Auth helpers
// ---------------------------------------------------------------------------

type StorageState = {
  origins?: Array<{
    localStorage?: Array<{ name: string; value: string }>
  }>
}

function getStoredAuthToken(): string | undefined {
  if (!existsSync(authFile)) return undefined
  try {
    const state = JSON.parse(readFileSync(authFile, 'utf8')) as StorageState
    for (const origin of state.origins || []) {
      const token = origin.localStorage?.find(e => e.name === 'auth_token')?.value
      if (token) return token
    }
  } catch (error) {
    console.warn(`[e2e cleanup] Could not read ${authFile}: ${(error as Error).message}`)
  }
  return undefined
}

async function requestOtpToken(email: string, otp: string): Promise<string | undefined> {
  const authApi = await request.newContext({ baseURL, ignoreHTTPSErrors: true })
  try {
    const reqRes = await authApi.post('/api/auth/otp/request', { data: { email } })
    if (!reqRes.ok()) {
      console.warn(`[e2e cleanup] OTP request failed for ${email}: ${reqRes.status()}`)
      return undefined
    }
    const verifyRes = await authApi.post('/api/auth/otp/verify', { data: { email, code: otp } })
    if (!verifyRes.ok()) {
      console.warn(`[e2e cleanup] OTP verify failed for ${email}: ${verifyRes.status()}`)
      return undefined
    }
    console.log(`[e2e cleanup] Authenticated as ${email}`)
    return ((await verifyRes.json()) as { token: string }).token
  } finally {
    await authApi.dispose()
  }
}

interface E2eUser {
  email: string
  otp: string
}

function discoverUsers(): E2eUser[] {
  const users: E2eUser[] = []

  for (let i = 1; i <= 9; i++) {
    const email = process.env[`TEST_USER_EMAIL_${i}`]
    const otp = process.env[`TEST_USER_OTP_${i}`]
    if (!email || !otp) continue
    users.push({ email, otp })
  }

  return users
}

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

type ProjectRow = { id: string; name: string; deployment_status?: string }

async function cleanupProjects(api: APIRequestContext): Promise<void> {
  const listRes = await api.get('/api/projects')
  if (!listRes.ok()) {
    console.warn(`[e2e cleanup] Could not list projects: ${listRes.status()}`)
    return
  }

  const body = (await listRes.json()) as { projects?: ProjectRow[] }
  const allProjects = body.projects || (body as unknown as ProjectRow[])
  const e2eProjects = allProjects.filter(p => E2E_PROJECT_PREFIX.test(p.name))

  for (const project of e2eProjects) {
    if (project.deployment_status?.toLowerCase() === 'ready') {
      const patchRes = await api.patch(
        `/api/projects/${project.id}/deployment-status?status=draft`
      )
      if (!patchRes.ok()) {
        console.warn(`[e2e cleanup] Could not unlock project "${project.name}": ${patchRes.status()}`)
        continue
      }
    }

    const delRes = await api.delete(`/api/projects/${project.id}`)
    if (delRes.ok() || delRes.status() === 404) {
      console.log(`[e2e cleanup] Deleted project: ${project.name}`)
    } else if (delRes.status() === 403) {
      console.warn(`[e2e cleanup] Skipped read-only project: ${project.name}`)
    } else {
      console.warn(`[e2e cleanup] Could not delete project "${project.name}": ${delRes.status()}`)
    }
  }

  if (e2eProjects.length === 0) {
    console.log('[e2e cleanup] No projects named E2E * found')
  }
}

type BoxRow = { id: string; name: string }

async function cleanupBoxes(api: APIRequestContext): Promise<void> {
  const listRes = await api.get('/api/boxes')
  if (!listRes.ok()) {
    console.warn(`[e2e cleanup] Could not list boxes: ${listRes.status()}`)
    return
  }

  const boxes = (await listRes.json()) as BoxRow[]
  const e2eBoxes = boxes.filter(b => E2E_BOX_PREFIX.test(b.name))

  for (const box of e2eBoxes) {
    const delRes = await api.delete(`/api/boxes/${box.id}`)
    if (delRes.ok() || delRes.status() === 404) {
      console.log(`[e2e cleanup] Deleted box: ${box.name}`)
    } else if (delRes.status() === 403) {
      console.warn(`[e2e cleanup] Skipped read-only box: ${box.name}`)
    } else {
      console.warn(`[e2e cleanup] Could not delete box "${box.name}": ${delRes.status()}`)
    }
  }

  if (e2eBoxes.length === 0) {
    console.log('[e2e cleanup] No boxes named e2e/* found')
  }
}

type ResourceSummary = { id: string; name: string }

async function cleanupResourceKind(api: APIRequestContext, kind: string): Promise<void> {
  const listRes = await api.get(`/api/${kind}`)
  if (!listRes.ok()) {
    console.warn(`[e2e cleanup] Could not list ${kind}: ${listRes.status()}`)
    return
  }

  const resources = (await listRes.json()) as ResourceSummary[]
  const e2eResources = resources.filter(r => E2E_RESOURCE_PREFIX.test(r.name))

  for (const resource of e2eResources) {
    const delRes = await api.delete(`/api/${kind}/${resource.id}`)
    if (delRes.ok() || delRes.status() === 404) {
      console.log(`[e2e cleanup] Deleted ${kind.slice(0, -1)}: ${resource.name}`)
    } else if (delRes.status() === 403) {
      console.warn(`[e2e cleanup] Skipped read-only ${kind.slice(0, -1)}: ${resource.name}`)
    } else {
      console.warn(`[e2e cleanup] Could not delete ${kind.slice(0, -1)} "${resource.name}": ${delRes.status()}`)
    }
  }

  if (e2eResources.length === 0) {
    console.log(`[e2e cleanup] No ${kind} named e2e-* found`)
  }
}

// ---------------------------------------------------------------------------
// Global teardown entry point
// ---------------------------------------------------------------------------

export default async function globalTeardown(): Promise<void> {
  if (process.env.E2E_CLEANUP === '0') {
    console.log('[e2e cleanup] Skipped because E2E_CLEANUP=0')
    return
  }

  const users = discoverUsers()

  if (users.length === 0) {
    console.warn('[e2e cleanup] No TEST_USER_EMAIL_1 set; cleanup will only see self-hosted/anonymous resources')
  }

  // Fallback: use stored auth token for first user
  const storedToken = getStoredAuthToken()

  for (const user of users) {
    console.log(`[e2e cleanup] Cleaning as ${user.email}`)

    const token = process.env.E2E_AUTH_TOKEN || storedToken || await requestOtpToken(user.email, user.otp)

    if (!token) {
      console.warn(`[e2e cleanup] Could not authenticate as ${user.email}; skipping`)
      continue
    }

    const api = await request.newContext({
      baseURL,
      ignoreHTTPSErrors: true,
      extraHTTPHeaders: { Authorization: `Bearer ${token}` },
    })

    try {
      await cleanupProjects(api)
      await cleanupBoxes(api)
      for (const kind of ['plugins', 'provisioners', 'triggers'] as const) {
        await cleanupResourceKind(api, kind)
      }
    } finally {
      await api.dispose()
    }
  }

  console.log('[e2e cleanup] Done')
}
