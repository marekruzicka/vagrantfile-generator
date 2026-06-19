# Running the Project — Environment Roles

Vagrantfile Generator has separate paths for development, self-hosted quick starts, local container smoke tests, and production deployments.

| Mode                | File/tool                           | Purpose                        |
| ------------------- | ----------------------------------- | ------------------------------ |
| Native dev          | `setup-local-dev.sh`, VS Code tasks | Active development             |
| Self-hosted Compose | `compose.yml`                       | End-user quick-start (prebuilt images) |
| Compose dev build   | `compose-dev.yml` + Makefile        | Local image build/smoke test   |
| Public production   | Helm chart ([helm-semver](https://github.com/rhysmcneill/helm-semver)) | Hosted Kubernetes deployment   |

## Native Dev

Runs backend and frontend natively with hot reload. See [local-setup.md](./local-setup.md) for full setup.

```bash
./setup-local-dev.sh
# Press F5 in VS Code, or:
cd backend && source .venv/bin/activate && uvicorn src.main:app --reload
cd frontend && npm run dev
```

URLs: http://localhost:5173 (frontend), http://localhost:8000 (backend), http://localhost:8000/docs (API docs)

## Self-Hosted Compose

End-user quick start using prebuilt GHCR images:

```bash
curl -fsSLO https://raw.githubusercontent.com/marekruzicka/vagrantfile-generator/refs/heads/master/compose.yml
podman-compose up -d
# or: docker compose up -d
```

- Runs in self-hosted mode by default
- Stores backend data in the `backend-data` named volume
- Exposes frontend on http://localhost:8080, proxies `/api` through it
- Backend not exposed directly

## Compose Dev Build

Builds local images for smoke testing:

```bash
make build && make up
make logs
make down
make clean  # removes volumes too
```

- Backend exposed on http://localhost:8000 for inspection
- Frontend on http://localhost:8080
- Bind-mounts `./backend/data` to `/app/data`
- Public-mode env vars can be supplied as optional overrides

## Public Production

Use the Helm chart for Kubernetes deployments with authentication enabled.

Chart releases are automated via [helm-semver](https://github.com/rhysmcneill/helm-semver):
- **CI (GHCR)**: Every push to `main` touching `helm/` triggers a chart release to `oci://ghcr.io/marekruzicka/helm-charts`.
- **Local (testing)**: Run `make helm-semver-release-local` to release to a local OCI registry.

Requires:

- `DEPLOYMENT_MODE=public`
- `JWT_SECRET` and `SESSION_COOKIE_SECRET`
- `BASE_URL` and `FRONTEND_URL`
- Mailgun and/or OIDC provider configuration

See [Authentication docs](../user/AUTHENTICATION.md).

## Troubleshooting

**CORS errors:**
- Native dev: ensure `CORS_ORIGINS=http://localhost:5173` in `backend/.env.local`
- Self-hosted Compose: `compose.yml` sets `CORS_ORIGINS=http://localhost:8080`

**Port conflicts:**
- Native dev: 5173, 8000
- Self-hosted Compose: 8080
- Compose dev build: 8080, 8000

**Data location:**
- Self-hosted Compose: named `backend-data` volume
- Compose dev build: `backend/data/`
