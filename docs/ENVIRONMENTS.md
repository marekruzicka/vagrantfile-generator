# Running the project — environment roles

Vagrantfile Generator has separate paths for active development, self-hosted quick starts, local container smoke tests, and public production deployments.

| Mode                | File/tool                           | Purpose                        |
| ------------------- | ----------------------------------- | ------------------------------ |
| Native dev          | `setup-local-dev.sh`, VS Code tasks | active development             |
| Self-hosted Compose | `compose.yml`                       | curl-only end-user quick-start |
| Compose dev build   | `compose-dev.yml` + Makefile        | local image build/smoke test   |
| Public production   | Helm chart                          | hosted Kubernetes deployment   |

---

## Native dev

Use this mode for day-to-day development and debugging.

**What it does:**

- Runs backend and frontend natively on your machine
- Backend uses `uvicorn --reload`
- Frontend uses the Vite dev server with hot module replacement
- Supports VS Code debugging and tasks

**Setup:**

```bash
./setup-local-dev.sh
```

**Run:**

- VS Code debugger: press `F5` and select the full-stack configuration
- VS Code tasks: run "Start Both Dev Servers"
- Manual terminals:

```bash
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

cd frontend
npm run dev
```

**URLs:**

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

---

## Self-hosted Compose

Use this mode for the end-user, curl-only quick start.

**What it does:**

- Pulls prebuilt `latest` images from GHCR
- Runs in self-hosted mode by default
- Stores backend data in the named `backend-data` volume
- Exposes only the frontend on http://localhost:8080
- Proxies API requests through the frontend at `/api`

**Quick start:**

```bash
curl -fsSLO https://raw.githubusercontent.com/marekruzicka/vagrantfile-generator/refs/heads/master/compose.yml
podman-compose up -d
# or: docker compose up -d
```

**Stop:**

```bash
podman-compose down
# or: docker compose down
```

---

## Compose dev build

Use this mode to build local images from the repository and smoke-test the containerized stack.

**What it does:**

- Builds backend and frontend images from local Dockerfiles
- Runs in self-hosted mode by default
- Exposes the backend on http://localhost:8000 for developer inspection
- Exposes the frontend on http://localhost:8080
- Bind-mounts `./backend/data` to `/app/data`
- Allows public-mode environment variables to be supplied as optional overrides

**Commands:**

```bash
make build
make up
make logs
make down
make clean
```

The Makefile auto-detects `podman-compose` and falls back to `docker compose`. All Compose targets use `compose-dev.yml`.

**URLs:**

- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Proxied API: http://localhost:8080/api

---

## Public production

Use the Helm chart for hosted Kubernetes deployments and public multi-user operation.

Public mode enables authentication and requires production secrets and provider configuration, such as:

- `DEPLOYMENT_MODE=public`
- `JWT_SECRET`
- `SESSION_COOKIE_SECRET`
- `BASE_URL`
- `FRONTEND_URL`
- Mailgun settings for email OTP, if enabled
- OIDC provider client IDs/secrets, if enabled

See [AUTHENTICATION.md](./AUTHENTICATION.md) for authentication configuration.

---

## Troubleshooting

**CORS errors:**

- Native dev: ensure `CORS_ORIGINS=http://localhost:5173` in `backend/.env.local`
- Self-hosted Compose: `compose.yml` sets `CORS_ORIGINS=http://localhost:8080`
- Compose dev build: override `CORS_ORIGINS` only if you change the frontend URL

**Port already in use:**

- Native dev uses ports 5173 and 8000
- Self-hosted Compose uses port 8080
- Compose dev build uses ports 8080 and 8000

**Data location:**

- Self-hosted Compose stores data in the named `backend-data` volume
- Compose dev build stores data under `backend/data`
