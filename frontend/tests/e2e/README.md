# E2E tests

This Playwright Test suite automates user-facing workflows from `docs/testing/TESTS.md`.

## Prerequisites

1. Install dependencies:

   ```bash
   cd frontend
   npm install
   npx playwright install chromium
   ```

2. Start the application in another terminal. For example, from the repository root:

   ```bash
   docker compose up --build
   ```

   The tests default to `http://localhost:8080`. Override it with `E2E_BASE_URL` if needed. Playwright is configured with `ignoreHTTPSErrors: true` so test environments with self-signed or otherwise untrusted TLS certificates can be tested.

## Run

From `frontend/`:

```bash
E2E_BASE_URL=http://localhost:8080 npm run test:e2e:dashboard
```

Run the whole E2E suite:

```bash
npm run test:e2e
```

Open the HTML report after a run:

```bash
npm run test:e2e:report
```

## Run tests selectively

All feature tests reuse the auth setup automatically. Tests that need a project create their own unique `E2E` project and clean it up, so suites are intended to be independently runnable.

Run one spec file:

```bash
E2E_BASE_URL=https://vgf.i.glide.sk:443 \
E2E_USER_EMAIL=test@glide.sk \
E2E_USER_OTP=123456 \
npx playwright test tests/e2e/vms.spec.ts
```

Run another suite by file:

```bash
npx playwright test tests/e2e/networking.spec.ts
npx playwright test tests/e2e/settings-boxes.spec.ts
npx playwright test tests/e2e/generated-vagrantfile.spec.ts
```

Run a single test by title or partial title:

```bash
npx playwright test -g "3.1 add a single VM"
npx playwright test -g "Generated Vagrantfile"
```

List all available tests without running them:

```bash
npm run test:e2e -- --list
```

Useful current spec files:

```text
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

## Public-mode login

If the app redirects to the login page, provide deterministic OTP credentials:

```bash
E2E_BASE_URL=http://localhost:8080 \
E2E_USER_EMAIL=test@glide.sk \
E2E_USER_OTP=123456 \
npm run test:e2e:dashboard
```

The setup test saves browser state to `frontend/.auth/user.json` for the feature tests.

## Notes

- Test data names are prefixed with `E2E` and include a unique suffix.
- Tests clean up projects they create through the UI when possible.
- The empty first-run test is skipped automatically when the target environment already has projects.
- Failure traces, screenshots, videos, and reports are written to Playwright's standard output folders.
