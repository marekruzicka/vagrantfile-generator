# Running the project — DEV, PROD, and USER modes

This document explains the three ways to run Vagrantfile Generator:

- **DEV** — local development running natively (no containers, fastest for development and debugging)
- **PROD** — production-like containerized setup with local builds (for testing production configuration)
- **USER** — distribution mode using prebuilt images from registry (for end users)

---

## DEV (Local Development — Recommended for Active Development)

**What it does:**

- Runs backend and frontend **natively on your machine** (not in containers)
- Backend runs with `uvicorn --reload` for instant code changes
- Frontend runs with Vite dev server for hot module replacement
- Full debugging support in VS Code with breakpoints
- Fastest iteration cycle for development

**Prerequisites:**

- Python 3.11+
- Node.js 18+
- npm

**Setup (first time only):**

```bash
./setup-local-dev.sh
```

This script will:

- Create Python virtual environment in `backend/.venv`
- Install Python dependencies
- Install Node.js dependencies
- Create necessary data directories
- Build initial Tailwind CSS

**Running the application:**

**Option 1: VS Code Debugger (Recommended)**

1. Open the project in VS Code
2. Press `F5` or go to "Run and Debug"
3. Select "Full Stack (Backend + Frontend)"
4. Set breakpoints and debug normally!

**Option 2: VS Code Tasks**

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type "Tasks: Run Task"
3. Select "Start Both Dev Servers"

**Option 3: Manual**

```bash
# Terminal 1 - Backend
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**URLs:**

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

**Configuration:**

- Backend: `backend/.env.local`
- Frontend: `frontend/.env.local`
- VS Code: `.vscode/settings.json`, `.vscode/launch.json`

**Notes:**

- Changes to Python code reload automatically
- Changes to frontend code update instantly with HMR
- Full debugging capabilities with breakpoints
- Tests can be run directly in VS Code
- **This is the fastest way to develop and debug**

---

## PROD (Production Build — For Testing Production Configuration)

**What it does:**

- Builds Docker/Podman images locally from source
- Runs backend with Gunicorn + Uvicorn workers (production-grade)
- Runs frontend with Nginx serving static files and proxying API
- Simulates production environment for testing

**Key files:** `compose-prod.yml`, `.env`

**Important environment variables:**

- `FE_LISTEN_URL` — the browser-facing URL (e.g., `http://localhost:8080`)
- Backend uses Gunicorn for concurrency
- Frontend Nginx proxies `/api` to backend

**Quick start:**

```bash
# Create .env file (or export variables)
echo "FE_LISTEN_URL=http://localhost:8080" > .env

# Build and run
make prod-up

# Or manually:
podman-compose -f compose-prod.yml up -d --build
```

**Other commands:**

```bash
make prod-build         # Just build images
make prod-down          # Stop containers
make prod-logs          # View logs
make prod-backend-logs  # Backend logs only
make prod-frontend-logs # Frontend logs only
make prod-clean         # Remove containers and volumes
```

**URLs:**

- Frontend: http://localhost:8080
- Backend: Internal only (accessed via frontend proxy at `/api`)

**Notes:**

- Code changes require rebuilding images (`make prod-up` rebuilds automatically)
- Use this to test production configuration before deployment
- Useful for smoke-testing the full stack
- Requires Podman or Docker installed

---

## USER (Distribution Mode — For End Users)

**What it does:**

- Uses **prebuilt images** from container registry
- No build step required — just pull and run
- Ideal for distribution and deployment

**Key file:** `compose.yml`

**Environment variables:**

- `FE_LISTEN_URL` — set this to your public URL (e.g., `http://myapp.example.com:8080`)
- Images are pulled from registry (defaults to GitHub Container Registry)

**Quick start:**

```bash
# Edit FE_LISTEN_URL in compose.yml or create .env
echo "FE_LISTEN_URL=http://localhost:8080" > .env

# Start
make user-up

# Or manually:
podman-compose up -d
```

**Other commands:**

```bash
make user-down   # Stop containers
make user-logs   # View logs
make user-clean  # Remove containers and volumes
```

**URLs:**

- Frontend: As configured in `FE_LISTEN_URL` (default: http://localhost:8080)
- Backend: Internal only

**Notes:**

- No build required — images are prebuilt
- Update `FE_LISTEN_URL` to match your deployment URL
- For custom domains, ensure DNS/hosts file is configured
- Data persists in named volume `backend-data`

---

## Comparison

| Feature            | DEV (Local)      | PROD (Build)        | USER (Prebuilt)         |
| ------------------ | ---------------- | ------------------- | ----------------------- |
| **Container**      | No               | Yes                 | Yes                     |
| **Build required** | No (native)      | Yes (local build)   | No (uses registry)      |
| **Code reload**    | Instant          | Requires rebuild    | N/A                     |
| **Debugging**      | Full breakpoints | Logs only           | Logs only               |
| **Performance**    | Fastest          | Production-like     | Production-like         |
| **Use case**       | Development      | Pre-deploy testing  | Distribution/Production |
| **Setup time**     | Fast (one-time)  | Medium (build time) | Fastest (pull only)     |

---

## Common Troubleshooting

**CORS errors:**

- DEV: Ensure `CORS_ORIGINS=http://localhost:5173` in `backend/.env.local`
- PROD/USER: Ensure `FE_LISTEN_URL` matches the browser URL you're using

**Backend not starting (DEV):**

- Check Python version: `python3 --version` (need 3.11+)
- Activate venv: `cd backend && source .venv/bin/activate`
- Check `.env.local` exists and has correct values
- Run `./setup-local-dev.sh` again

**Frontend not starting (DEV):**

- Check Node.js version: `node --version` (need 18+)
- Run `cd frontend && npm install`
- Check `.env.local` has correct `VITE_BROWSER_API_URL`

**Can't connect to custom domain (PROD/USER):**

- Add domain to `/etc/hosts` pointing to container host IP
- Verify `FE_LISTEN_URL` in environment matches domain

**Port already in use:**

- DEV: Check if other services are using 8000 or 5173
- PROD/USER: Check if other services are using 8080 or 8000
