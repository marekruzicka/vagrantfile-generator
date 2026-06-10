# E2E test proof of concept

This is a Playwright Test proof of concept for `docs/testing/TESTS.md` section **2. Projects Dashboard**.

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
