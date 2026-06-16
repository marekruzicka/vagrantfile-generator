# Local Development Setup

This guide covers setting up and running Vagrantfile Generator natively (without containers) for the best development and debugging experience.

## Why Native Development?

- ✅ Instant code changes — no image rebuilds
- ✅ Full debugging — breakpoints, variable inspection, step-through
- ✅ Hot reload for both backend and frontend
- ✅ Better IDE integration — IntelliSense, code navigation, refactoring

## Prerequisites

- **Python 3.11+** — Backend runtime
- **Node.js 18+** — Frontend runtime
- **npm** — Package manager
- **VS Code** (recommended) — Debug configurations included

```bash
python3 --version   # 3.11+
node --version      # v18+
npm --version
```

## First-Time Setup

```bash
./setup-local-dev.sh
```

This script:
- Creates Python virtual environment (`backend/.venv`)
- Installs Python and Node.js dependencies
- Creates data directories and initializes auth data
- Builds Tailwind CSS

### Environment Variables

Setup creates `.env.local` files with defaults. Customize if needed:

**Backend** (`backend/.env.local`):
```bash
DEPLOYMENT_MODE=self-hosted
JWT_SECRET=local-dev-jwt-secret-key-change-this-min-32-chars
SESSION_COOKIE_SECRET=local-dev-session-cookie-secret-change-this-min-32-chars
CORS_ORIGINS=http://localhost:5173
FRONTEND_URL=http://localhost:5173
BASE_URL=http://localhost:8000
```

**Frontend** (`frontend/.env.local`):
```bash
VITE_API_URL=http://localhost:8000
VITE_BROWSER_API_URL=http://localhost:8000
```

## Running

### Option 1: VS Code Debugger (Recommended)

Press **F5** → select **"Full Stack (Backend + Frontend)"**. Both servers start with full debugging support.

### Option 2: VS Code Tasks

`Ctrl+Shift+P` → "Tasks: Run Task" → "Start Both Dev Servers"

### Option 3: Manual

```bash
# Terminal 1 — Backend
cd backend && source .venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

**URLs:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Compose Dev Build

For local image build and containerized smoke testing:

```bash
make build    # Build images
make up       # Start containers
make logs     # View logs
make down     # Stop
make clean    # Remove containers and volumes
```

Uses `compose-dev.yml`. Exposes frontend on http://localhost:8080 and backend on http://localhost:8000.

## Running Tests

```bash
# All tests
cd backend && source .venv/bin/activate && pytest tests/ -v

# Specific file
pytest tests/integration/test_auth.py -v

# With coverage
pytest --cov=src --cov-report=html

# E2E tests (Playwright) — see docs/dev/testing/e2e-guide.md
cd frontend && npx playwright test
```

## Project Structure

```
vagrantfile-generator/
├── backend/
│   ├── .venv/              # Python virtual environment (local only)
│   ├── src/
│   │   ├── main.py         # FastAPI entry point
│   │   ├── api/            # Route handlers
│   │   ├── services/       # Business logic
│   │   ├── models/         # Data models
│   │   └── utils/          # Utilities
│   ├── tests/              # Backend tests
│   ├── data/               # Runtime data (gitignored for users/)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── index.html
│   │   ├── js/             # JavaScript modules
│   │   ├── components/     # Reusable components
│   │   ├── views/          # Page views
│   │   ├── modals/         # Modal dialogs
│   │   └── styles/         # CSS (Tailwind)
│   ├── tests/e2e/          # Playwright E2E tests
│   ├── package.json
│   └── vite.config.js
├── .vscode/                # Debug configs, tasks, recommended extensions
└── setup-local-dev.sh      # Automated setup
```

## Common Issues

### Port already in use
```bash
lsof -i :8000 && lsof -i :5173
kill -9 <PID>
```

### Module not found
```bash
cd backend && source .venv/bin/activate && pip install -r requirements.txt
```

### CORS errors
Ensure `backend/.env.local` has `CORS_ORIGINS=http://localhost:5173`

### Dependencies out of date
```bash
cd backend && source .venv/bin/activate && pip install -r requirements.txt --upgrade
cd frontend && npm install
```

## Adding Dependencies

```bash
# Python
cd backend && source .venv/bin/activate
pip install <package> && pip freeze > requirements.txt

# Node
cd frontend && npm install <package>
```
