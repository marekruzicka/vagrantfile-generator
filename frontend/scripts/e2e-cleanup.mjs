import { request } from '@playwright/test'
import { existsSync, readFileSync } from 'node:fs'

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const baseURL = process.env.E2E_BASE_URL || 'http://localhost:8080'
const authFile = '.auth/user.json'

// ---------------------------------------------------------------------------
// Naming conventions used by E2E tests (see test-data.ts and spec files)
// ---------------------------------------------------------------------------
const E2E_PROJECT_PREFIX = /^E2E /i           // uniqueProjectName("Foo")  → "E2E Foo …"
const E2E_BOX_PREFIX = /^e2e[/-]/i            // boxes named "e2e/box-…"
const E2E_RESOURCE_PREFIX = /^e2e-/i          // plugins, provisioners, triggers

// ---------------------------------------------------------------------------
// Auth helpers
// ---------------------------------------------------------------------------

/** Read cached token from Playwright auth state file. */
function getStoredAuthToken() {
  if (!existsSync(authFile)) return undefined
  try {
    const state = JSON.parse(readFileSync(authFile, 'utf8'))
    for (const origin of state.origins || []) {
      const token = origin.localStorage?.find(e => e.name === 'auth_token')?.value
      if (token) return token
    }
  } catch (error) {
    console.warn(`[e2e cleanup] Could not read ${authFile}: ${error.message}`)
  }
  return undefined
}

/** Log in via OTP and return a Bearer token. */
async function requestOtpToken(email, otp) {
  const authApi = await request.newContext({ baseURL, ignoreHTTPSErrors: true })
  try {
    // Request OTP
    const reqRes = await authApi.post('/api/auth/otp/request', { data: { email } })
    if (!reqRes.ok()) {
      console.warn(`[e2e cleanup] OTP request failed for ${email}: ${reqRes.status()}`)
      return undefined
    }
    // Verify OTP
    const verifyRes = await authApi.post('/api/auth/otp/verify', { data: { email, code: otp } })
    if (!verifyRes.ok()) {
      console.warn(`[e2e cleanup] OTP verify failed for ${email}: ${verifyRes.status()}`)
      return undefined
    }
    console.log(`[e2e cleanup] Authenticated as ${email}`)
    return (await verifyRes.json()).token
  } finally {
    await authApi.dispose()
  }
}

/**
 * Discover E2E users from environment variables.
 *
 * Supported patterns (listed in test-run order):
 *   E2E_USER_EMAIL          / E2E_USER_OTP           → user 0
 *   E2E_USER_EMAIL_1        / E2E_USER_OTP_1         → user 1  (fallback OTP: E2E_USER_OTP)
 *   E2E_USER_EMAIL_2        / E2E_USER_OTP_2         → user 2  (fallback OTP: E2E_USER_OTP)
 */
function discoverUsers() {
  const users = []
  const defaultOtp = process.env.E2E_USER_OTP || '123456'

  // User 0
  const email0 = process.env.E2E_USER_EMAIL
  if (email0) users.push({ email: email0, otp: process.env.E2E_USER_OTP || defaultOtp })

  // User 1..9
  for (let i = 1; i <= 9; i++) {
    const email = process.env[`E2E_USER_EMAIL_${i}`]
    if (!email) continue
    const otp = process.env[`E2E_USER_OTP_${i}`] || defaultOtp
    users.push({ email, otp })
  }

  return users
}

// ---------------------------------------------------------------------------
// API cleanup helpers
// ---------------------------------------------------------------------------

async function cleanupProjects(api) {
  const listRes = await api.get('/api/projects')
  if (!listRes.ok()) {
    console.warn(`[e2e cleanup] Could not list projects: ${listRes.status()}`)
    return
  }

  const body = await listRes.json()
  const allProjects = body.projects || body
  const e2eProjects = allProjects.filter(p => E2E_PROJECT_PREFIX.test(p.name))

  for (const project of e2eProjects) {
    // Unlock Ready projects before deleting
    if (project.deployment_status?.toLowerCase() === 'ready') {
      const patchRes = await api.patch(
        `/api/projects/${project.id}/deployment-status?status=draft`
      )
      if (!patchRes.ok()) {
        console.warn(
          `[e2e cleanup] Could not unlock project "${project.name}": ${patchRes.status()}`
        )
        continue
      }
    }

    const delRes = await api.delete(`/api/projects/${project.id}`)
    if (delRes.ok() || delRes.status() === 404) {
      console.log(`[e2e cleanup] Deleted project: ${project.name}`)
    } else if (delRes.status() === 403) {
      console.warn(`[e2e cleanup] Skipped read-only project: ${project.name}`)
    } else {
      console.warn(
        `[e2e cleanup] Could not delete project "${project.name}": ${delRes.status()}`
      )
    }
  }

  if (e2eProjects.length === 0) {
    console.log('[e2e cleanup] No projects named E2E * found')
  }
}

async function cleanupBoxes(api) {
  const listRes = await api.get('/api/boxes')
  if (!listRes.ok()) {
    console.warn(`[e2e cleanup] Could not list boxes: ${listRes.status()}`)
    return
  }

  const boxes = await listRes.json()
  const e2eBoxes = boxes.filter(b => E2E_BOX_PREFIX.test(b.name))

  for (const box of e2eBoxes) {
    const delRes = await api.delete(`/api/boxes/${box.id}`)
    if (delRes.ok() || delRes.status() === 404) {
      console.log(`[e2e cleanup] Deleted box: ${box.name}`)
    } else if (delRes.status() === 403) {
      console.warn(`[e2e cleanup] Skipped read-only box: ${box.name}`)
    } else {
      console.warn(
        `[e2e cleanup] Could not delete box "${box.name}": ${delRes.status()}`
      )
    }
  }

  if (e2eBoxes.length === 0) {
    console.log('[e2e cleanup] No boxes named e2e/* found')
  }
}

async function cleanupResourceKind(api, kind) {
  const listRes = await api.get(`/api/${kind}`)
  if (!listRes.ok()) {
    console.warn(`[e2e cleanup] Could not list ${kind}: ${listRes.status()}`)
    return
  }

  const resources = await listRes.json()
  const e2eResources = resources.filter(r => E2E_RESOURCE_PREFIX.test(r.name))

  for (const resource of e2eResources) {
    const delRes = await api.delete(`/api/${kind}/${resource.id}`)
    if (delRes.ok() || delRes.status() === 404) {
      console.log(`[e2e cleanup] Deleted ${kind.slice(0, -1)}: ${resource.name}`)
    } else if (delRes.status() === 403) {
      console.warn(`[e2e cleanup] Skipped read-only ${kind.slice(0, -1)}: ${resource.name}`)
    } else {
      console.warn(
        `[e2e cleanup] Could not delete ${kind.slice(0, -1)} "${resource.name}": ${delRes.status()}`
      )
    }
  }

  if (e2eResources.length === 0) {
    console.log(`[e2e cleanup] No ${kind} named e2e-* found`)
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

const users = discoverUsers()

if (users.length === 0) {
  // Self-hosted / no env vars — use stored auth token if available
  console.warn(
    '[e2e cleanup] No E2E_USER_EMAIL set; trying stored auth token or anonymous access'
  )
}

let authToken = getStoredAuthToken()

for (const user of users) {
  console.log(`[e2e cleanup] Cleaning as ${user.email}`)

  const token = process.env.E2E_AUTH_TOKEN || await requestOtpToken(user.email, user.otp)

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
    for (const kind of ['plugins', 'provisioners', 'triggers']) {
      await cleanupResourceKind(api, kind)
    }
  } finally {
    await api.dispose()
  }
}

console.log('[e2e cleanup] Done')
