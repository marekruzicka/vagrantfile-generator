# Running the project — DEV and PROD

This document explains the three common ways to deploy Vagrantfile Generator:

- **DEV** (fast local development using source mounts and auto-reload)
- **PROD (build)** — build images locally and run a production-like stack
- **PROD (prebuilt)** — run using prebuilt images via `docker-compose.yml` (useful for distribution)

### DEV (recommended for iterative development)

- **What it does:**
  - Builds a backend dev image but mounts your local `backend/` code into the container.
  - Runs the backend with `uvicorn --reload` so code changes apply immediately.
  - Runs the frontend using the development Dockerfile (Vite dev server) with hot reload.

- **Key file:** `docker-compose-dev.yml`

- Important environment variables (examples in the compose file):
  - `CORS_ORIGINS=http://localhost:5173` (backend) — allow the Vite dev frontend
  - `VITE_API_URL` and `VITE_BROWSER_API_URL` (frontend) — internal proxy target vs browser-facing API URL

- **Quick start:**
```bash
podman-compose -f docker-compose-dev.yml up -d --build
# open http://localhost:5173 in your browser
```

**Notes:**
- Source is mounted into containers so you don't need to rebuild to see code changes.
- Use this mode for feature development and debugging.

---

### PROD (build locally — production-like)

- **What it does:**
  - Builds the backend and frontend images from `backend/Dockerfile` and `frontend/Dockerfile`.
  - Backend uses Gunicorn with Uvicorn workers for concurrency.
  - Frontend is served by Nginx and proxies `/api` to the backend.
  - `FE_LISTEN_URL` is used to configure Nginx `server_name` and backend CORS origins.

- **Key file:** `docker-compose-prod.yml`

- Important environment variables (set in the compose or overridden in your environment):
  - `FE_LISTEN_URL` — the browser-facing URL for the frontend (e.g., `http://notas.lan:8080`).
  - `FRONTEND_API_URL` — usually `/api` (the Nginx proxy path to backend).

- **Quick start (build & run):**
```bash
podman-compose -f docker-compose-prod.yml up -d --build
# visit the FE_LISTEN_URL (e.g. http://notas.lan:8080). Ensure your hosts file points notas.lan to the host running the containers.
```

**Notes:**
- Because the code is copied into the image, changes require rebuilding images.
- Ideal for smoke-testing a production-like stack locally.

---

### PROD (prebuilt images / distribution)

- **What it does:**
  - Uses prebuilt images (image tags configured in `docker-compose.yml`) and does not require a local build.
  - Useful for packaging and distributing a runnable stack; you only need to set `FE_LISTEN_URL` appropriately.

- **Key file:** `docker-compose.yml`

- **Quick start (using prebuilt images):**
```bash
# Edit docker-compose.yml to set FE_LISTEN_URL if needed, then:
podman-compose up -d
# browse to the FE_LISTEN_URL (e.g. http://localhost:8080)
```

**Notes:**
- Backend CORS is set from `FE_LISTEN_URL` in the compose file; ensure your frontend host is allowed.
- This mode assumes images `vagrantfile-backend:prod` and `vagrantfile-frontend:prod` are available locally (or from your registry if you update image references).

---

**Common troubleshooting**

- CORS errors: ensure `CORS_ORIGINS` (dev) or `FE_LISTEN_URL` (prod) include the browser origin you are using.
- Missing hostnames: if FE_LISTEN_URL uses a custom domain (not localhost), add it to `/etc/hosts` pointing to the host IP.
- Not seeing code changes in prod: rebuild images; prod containers copy code at build time.
