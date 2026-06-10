# E2E Test Automation Approach

This document describes the recommended automated end-to-end testing approach for Vagrantfile Generator. It is intended as implementation guidance for future developers or AI agents creating the browser test suite.

## Recommendation

Use **Playwright Test with TypeScript** for user-facing end-to-end tests.

Playwright is preferred over Selenium for this application because it provides:

- Reliable auto-waiting for dynamic UI updates
- First-class support for Chromium, Firefox, and WebKit
- Built-in screenshots, videos, traces, and HTML reports
- Easy authentication state reuse
- Less boilerplate and fewer flaky waits than Selenium
- Good fit for Alpine.js-driven frontend interactions

The goal is to automate the user-based scenarios defined in [`TESTS.md`](./TESTS.md), interacting with the running application through the browser only.

## Scope

E2E tests should validate behavior from the user's point of view:

- Login and session handling
- Project dashboard workflows
- Project detail workflows
- VM creation/editing/deletion
- Networking configuration
- Boxes, plugins, provisioners, and triggers in Settings
- Project-level assignment of global resources
- Generated Vagrantfile preview/copy behavior
- Public-mode shared resource permissions
- Multi-user data isolation
- Ready/Draft project locking behavior

E2E tests should **not** directly test backend service code, internal frontend functions, or implementation details unless needed for setup/cleanup.

## Suggested Test Stack

```text
Playwright Test
TypeScript
Node.js
```

Suggested dependencies:

```bash
npm install -D @playwright/test typescript
npx playwright install
```

## Suggested Directory Structure

```text
tests/e2e/
  auth.setup.ts
  auth.spec.ts
  projects-dashboard.spec.ts
  project-detail.spec.ts
  vms.spec.ts
  networking.spec.ts
  settings-boxes.spec.ts
  settings-plugins.spec.ts
  settings-provisioners.spec.ts
  settings-triggers.spec.ts
  project-plugins.spec.ts
  project-provisioners.spec.ts
  project-triggers.spec.ts
  generated-vagrantfile.spec.ts
  shared-resources.spec.ts
  multi-user-isolation.spec.ts
  smoke.spec.ts
  fixtures/
    test-data.ts
  pages/
    LoginPage.ts
    ProjectsPage.ts
    ProjectDetailPage.ts
    SettingsPage.ts
playwright.config.ts
```

## Test Configuration

Use environment variables for deployment-specific settings:

```bash
E2E_BASE_URL=http://localhost:8080
E2E_USER_EMAIL=test@glide.sk
E2E_USER_OTP=123456
E2E_SECOND_USER_EMAIL=test2@glide.sk
E2E_SECOND_USER_OTP=123456
```

Example `playwright.config.ts` concepts:

- Base URL from `E2E_BASE_URL`
- Run Chromium by default in CI
- Optionally run Firefox/WebKit in nightly builds
- Enable trace on failure
- Capture screenshot on failure
- Capture video on failure or retry
- Use a saved auth state for authenticated tests

Recommended defaults:

```ts
use: {
  baseURL: process.env.E2E_BASE_URL || 'http://localhost:8080',
  ignoreHTTPSErrors: true,
  trace: 'retain-on-failure',
  screenshot: 'only-on-failure',
  video: 'retain-on-failure'
}
```

`ignoreHTTPSErrors: true` is useful for internal/test deployments using self-signed or otherwise untrusted TLS certificates. Do not treat it as evidence that production TLS is correctly configured.

The current proof of concept lives under `frontend/`, so run commands from that directory unless a root-level package script is added later:

```bash
cd frontend
E2E_BASE_URL=https://vgf.i.glide.sk:443 \
E2E_USER_EMAIL=test@glide.sk \
E2E_USER_OTP=123456 \
npm run test:e2e:dashboard
```

## Authentication Strategy

Most tests require an authenticated public-mode session. Avoid repeating login in every test.

Recommended flow:

1. Create `auth.setup.ts`
2. Open login page
3. Enter `E2E_USER_EMAIL`
4. Request OTP
5. Enter `E2E_USER_OTP`
6. Wait for Projects page
7. Save Playwright storage state to `.auth/user.json`
8. Reuse `.auth/user.json` in authenticated test projects

Example concept:

```ts
await page.goto('/');
await page.getByRole('textbox', { name: /email address/i }).fill(email);
await page.getByRole('button', { name: /send login code/i }).click();
await page.getByRole('textbox', { name: /enter 6-digit code/i }).fill(otp);
await page.getByRole('button', { name: /verify code/i }).click();
await expect(page.getByRole('heading', { name: /your vagrant projects/i })).toBeVisible();
await page.context().storageState({ path: '.auth/user.json' });
```

In public mode, the app may first load `/`, run deployment/auth checks, and then redirect to `/views/login/login.html`. The setup test should not assume the login form is immediately visible. Wait for either the Projects page or the Login page, then branch:

```ts
async function waitForEntryState(page, projectsHeading, emailField) {
  const deadline = Date.now() + 20_000;

  while (Date.now() < deadline) {
    if (await projectsHeading.isVisible().catch(() => false)) return 'projects';
    if (await emailField.isVisible().catch(() => false)) return 'login';
    await page.waitForTimeout(250);
  }

  throw new Error(`Timed out waiting for Projects or Login page. Current URL: ${page.url()}`);
}
```

After OTP verification, wait for the Projects heading with a generous timeout before saving storage state.

For CI and repeatable test runs, prefer a non-production/test deployment with a deterministic OTP such as `123456`. Do not depend on real email delivery for every automated run.

## Test Data Strategy

Use unique names per test run to avoid collisions:

```ts
const runId = Date.now();
const projectName = `E2E Project ${runId}`;
```

Recommended practices:

- Prefix test data with `E2E` for easy identification
- Clean up created projects/resources after each test when possible
- If cleanup fails, use unique names so later tests are not blocked
- Keep tests independent; do not depend on previous spec files unless explicitly using setup fixtures

## Page Object Model

Use lightweight page objects for repeated flows, not excessive abstraction.

Good candidates:

- `LoginPage`
- `ProjectsPage`
- `ProjectDetailPage`
- `SettingsPage`

Page objects should expose user actions and assertions, for example:

```ts
await projectsPage.createProject(name, description);
await projectsPage.expectProjectVisible(name);
await projectsPage.filterReady();
await projectDetailPage.changeStatus('ready');
```

Avoid page objects that mirror implementation details or CSS structure too closely.

## Selector Strategy

Prefer stable, accessible selectors:

1. `getByRole()` with accessible name
2. `getByLabel()` for form fields
3. `getByText()` for visible user-facing text
4. `data-testid` only where accessible selectors are not stable enough

Recommended future improvement: add `data-testid` attributes for complex repeated UI cards and modal actions, for example:

```html
<div data-testid="project-card">
<button data-testid="delete-project-button">...</button>
```

Avoid brittle selectors such as long CSS chains or positional selectors unless there is no alternative.

### Selector Lessons from the Projects Dashboard POC

The Alpine frontend keeps some hidden views/modal markup in the DOM. Playwright strict mode still sees hidden or duplicate elements unless locators are scoped carefully. Do not rely on broad `page.getByText(...)` for repeated names, descriptions, statuses, or buttons.

Patterns that worked well in the POC:

- Scope assertions to `main`, `banner`, a specific card, or a modal before matching text.
- Use exact accessible names when one label is a substring of another.
- For modals, locate the modal container first, then use scoped assertions/buttons.
- For repeated project descriptions, scope to the visible project detail header or target project card.
- For controls that appear in both header and page content, scope to `getByRole('banner')` or `getByRole('main')`.

Examples:

```ts
// Good: empty-state step heading, not the Create Project submit button.
await expect(
  page.getByRole('main').getByRole('heading', { name: 'Create Project' })
).toBeVisible();

// Good: delete confirmation scoped to the active modal.
const dialog = page.locator('.modal-content').filter({
  has: page.getByRole('heading', { name: /confirm deletion/i }),
});
await expect(dialog).toContainText(projectName);
await dialog.getByRole('button', { name: /^delete$/i }).click();

// Good: project detail header found from the visible heading, avoiding hidden dashboard cards.
const main = page.getByRole('main');
const projectHeading = main.getByRole('heading', { name: projectName });
const projectHeader = projectHeading.locator(
  'xpath=ancestor::div[contains(@class, "card")][1]'
);
await expect(projectHeader).toContainText(description);

// Good: distinguish duplicate Add VM controls.
await expect(
  page.getByRole('banner').getByRole('button', { name: /^add vm$/i })
).toBeVisible();

// Good: avoid matching "No virtual machines configured".
await expect(
  main.getByRole('heading', { name: 'Virtual Machines', exact: true })
).toBeVisible();
```

Use `.first()` only when any visible match is acceptable. If the assertion is about a specific UI region, scope the locator instead.

## Test Grouping

Start with a small smoke suite, then expand by feature.

### Smoke Suite

Run on every deployment:

1. Login
2. Create project
3. Open project detail
4. Add one VM
5. Generate Vagrantfile
6. Delete project

### Feature Suites

Map directly to `TESTS.md` sections:

- `projects-dashboard.spec.ts` → Section 2
- `vms.spec.ts` → Section 3
- `networking.spec.ts` → Section 4
- `settings-boxes.spec.ts` → Section 5
- `settings-plugins.spec.ts` → Section 6
- `project-plugins.spec.ts` → Section 7
- `settings-provisioners.spec.ts` → Section 8
- `project-provisioners.spec.ts` → Section 9
- `settings-triggers.spec.ts` → Section 10
- `project-triggers.spec.ts` → Section 11
- `shared-resources.spec.ts` → Section 12
- `generated-vagrantfile.spec.ts` → Section 13

## Suggested First Implementation Target

Start by automating the already manually verified Section 2 tests:

```text
projects-dashboard.spec.ts
```

Implement these tests first:

1. Empty first-run/dashboard state where applicable
2. Create project
3. Stats and filters
4. Open project detail
5. Delete draft project including cancel behavior
6. Ready project protection and Draft restore

This provides immediate value and validates the main navigation and project lifecycle.

The current proof of concept implements this target in:

```text
frontend/playwright.config.ts
frontend/tests/e2e/auth.setup.ts
frontend/tests/e2e/projects-dashboard.spec.ts
frontend/tests/e2e/fixtures/test-data.ts
frontend/tests/e2e/pages/ProjectsPage.ts
frontend/tests/e2e/pages/ProjectDetailPage.ts
frontend/tests/e2e/README.md
```

Build future suites by following the same shape: small spec files mapped to `TESTS.md`, lightweight page objects, unique `E2E`-prefixed test data, and `try/finally` cleanup.

## CI Recommendations

Run E2E tests against a real running application.

Suggested CI flow:

1. Build/start app with Docker Compose or Helm test environment
2. Wait for frontend/backend health
3. Run Playwright auth setup
4. Run smoke tests
5. Upload Playwright HTML report, traces, screenshots, and videos on failure
6. Tear down environment

Useful commands:

```bash
# From frontend/
npm run test:e2e
npm run test:e2e:dashboard
npm run test:e2e:report

# Direct Playwright commands also work from frontend/
npx playwright test
npx playwright test tests/e2e/smoke.spec.ts
npx playwright show-report
```

Recommended CI artifact paths:

```text
playwright-report/
test-results/
.auth/  # do not upload if it contains real tokens
```

## Handling Public Mode and Multi-User Tests

For public-mode tests:

- Use at least two test users
- Save separate auth states:
  - `.auth/user-a.json`
  - `.auth/user-b.json`
- Verify user A cannot see user B's private projects/resources
- Verify both users can see shared resources
- Verify shared resources are read-only
- Verify copied shared resources become editable personal resources

Multi-user tests should use separate browser contexts, not just logout/login in one context.

## Known Current Frontend Issue to Watch

Manual Playwright testing observed repeated console errors during initial render:

- AlpineJS null reference warnings for `editingVM.*`
- Unhandled `Script error` messages from `main.js`

E2E tests should initially tolerate these if workflows still pass, but a separate quality gate should eventually fail tests on unexpected console errors after the frontend issues are fixed.

Recommended phased approach:

1. Phase 1: Log console errors but do not fail tests
2. Phase 2: Allowlist known errors only
3. Phase 3: Fail on any unexpected console error

## Cleanup Strategy

Tests should clean up resources they create when possible:

- Delete created projects at the end of each test
- Delete created boxes/plugins/provisioners/triggers if the test created them
- Use `try/finally` cleanup blocks
- Make cleanup locators as robust as the test locators; failed cleanup leaves `E2E` resources behind and can make later selector failures harder to diagnose
- If a test changes a project to Ready, switch it back to Draft before attempting UI deletion because Ready projects intentionally disable destructive actions

If UI cleanup is unreliable, provide a test-only cleanup endpoint or reset fixture in non-production environments. Do not use test-only cleanup endpoints in production.

## Reporting

Use Playwright's built-in HTML report as the primary automated report.

Each test should have clear names matching `TESTS.md`, for example:

```ts
test('2.2 create project: project appears as Draft and stats update', async ({ page }) => {
  // ...
});
```

On failure, Playwright should retain:

- Screenshot
- Trace
- Video if enabled
- Console logs
- Network errors where useful

## Summary

Use **Playwright Test + TypeScript** as the standard E2E testing framework. Implement tests from `TESTS.md` as browser-driven user workflows, starting with the Project Dashboard tests. Use saved authentication state, unique test data, accessible selectors, and Playwright traces/screenshots for debugging.
