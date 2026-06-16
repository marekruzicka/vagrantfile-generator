# E2E Testing Guide

End-to-end tests use **Playwright Test with TypeScript**, automating user workflows from [test-plan.md](./test-plan.md) by interacting with the running application through a browser only.

## Prerequisites

```bash
make up

cd frontend
npm install
npx playwright install chromium firefox
```

Start the application in another terminal (e.g., `docker compose up`). Tests default to `http://localhost:8080` — override with `E2E_BASE_URL`.

## Running Tests

From `frontend/`:

```bash
# Full suite (public mode with multi-user isolation)
E2E_BASE_URL=http://localhost:8080 \
TEST_USER_EMAIL_1=test@glide.sk \
TEST_USER_OTP_1=123456 \
TEST_USER_EMAIL_2=test1@glide.sk \
TEST_USER_OTP_2=123456 \
npm run test:e2e

# Single spec file
npx playwright test tests/e2e/vms.spec.ts

# Single test by title
npx playwright test -g "3.1 add a single VM"

# List all tests
npx playwright test --list

# Open HTML report
npm run test:e2e:report
```

Spec files:

```
tests/e2e/projects-dashboard.spec.ts
tests/e2e/vms.spec.ts
tests/e2e/networking.spec.ts
tests/e2e/settings-boxes.spec.ts
tests/e2e/settings-plugins.spec.ts
tests/e2e/project-plugins.spec.ts
tests/e2e/settings-provisioners.spec.ts
tests/e2e/project-provisioners.spec.ts
tests/e2e/settings-triggers.spec.ts
tests/e2e/project-triggers.spec.ts
tests/e2e/shared-resources.spec.ts
tests/e2e/generated-vagrantfile.spec.ts
tests/e2e/application-settings.spec.ts
```

## Authentication

In public mode, the auth setup (`tests/e2e/auth.setup.ts`) saves browser state to `frontend/.auth/user.json`. Feature tests reuse this state automatically.

For deterministic OTP in test environments, configure static test users via backend env vars. See [SETUP_EMAIL_OTP.md](../user/SETUP_EMAIL_OTP.md#test-users-development-only).

## Test Data

- All test data uses `E2E` or `e2e-` prefixes with unique suffixes
- Tests clean up created projects through the UI when possible
- Global teardown deletes user-owned plugins, provisioners, and triggers named `e2e-*`
- Set `E2E_CLEANUP=0` to disable cleanup for debugging
- Tests are independent — each creates its own project

## Selector Strategy

Prefer stable, accessible selectors (in order):

1. `getByRole()` with accessible name
2. `getByLabel()` for form fields
3. `getByText()` for visible text
4. `data-testid` only as a last resort

Scope assertions to specific regions (`main`, `banner`, modal containers) — the Alpine.js frontend keeps hidden markup in the DOM. Avoid broad `page.getByText()` for repeated names.

Good patterns:

```ts
// Scope to visible modal
const dialog = page.locator(".modal-content").filter({
  has: page.getByRole("heading", { name: /confirm deletion/i }),
});
await dialog.getByRole("button", { name: /^delete$/i }).click();

// Distinguish header vs page controls
await page.getByRole("banner").getByRole("button", { name: /^add vm$/i });
```

## Configuration

```ts
// playwright.config.ts defaults
{
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:8080',
    ignoreHTTPSErrors: true,      // for self-signed certs in test deployments
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  }
}
```

## CI Recommendations

1. Build/start app with Docker Compose or Helm
2. Wait for frontend/backend health
3. Run Playwright auth setup
4. Run tests
5. Upload Playwright report, traces, screenshots on failure
6. Tear down environment

## Console Error Policy

Phased approach for handling browser console errors:

1. **Phase 1 (current)**: Log console errors but don't fail tests
2. **Phase 2**: Allowlist known errors only
3. **Phase 3**: Fail on any unexpected console error
