# Local Development Guide

This guide explains how to set up and run Vagrantfile Generator locally (without containers) for the best development and debugging experience.

## Why Develop Locally?

Running the application natively on your machine (not in containers) provides:

✅ **Instant code changes** — No rebuilding images  
✅ **Full debugging** — Set breakpoints, inspect variables, step through code  
✅ **Faster iteration** — Hot reload for both backend and frontend  
✅ **Better IDE integration** — Full IntelliSense, code navigation, refactoring  
✅ **Easier testing** — Run and debug tests directly in VS Code

## Prerequisites

- **Python 3.11+** — Backend runtime
- **Node.js 18+** — Frontend runtime
- **npm** — Package manager (comes with Node.js)
- **VS Code** (recommended) — Best IDE support with provided configurations

Check versions:

```bash
python3 --version   # Should be 3.11 or higher
node --version      # Should be v18 or higher
npm --version
```

## First-Time Setup

### 1. Run the Setup Script

The project includes an automated setup script that configures everything:

```bash
./setup-local-dev.sh
```

This script will:

- ✅ Create Python virtual environment (`backend/.venv`)
- ✅ Install Python dependencies
- ✅ Install Node.js dependencies
- ✅ Create data directories
- ✅ Initialize auth data files
- ✅ Build Tailwind CSS
- ✅ Verify prerequisites

**Expected output:** Green checkmarks and a success message with next steps.

### 2. Configure Environment Variables

The setup script creates `.env.local` files with sensible defaults. Review and customize if needed:

**Backend** (`backend/.env.local`):

```bash
DEPLOYMENT_MODE=self-hosted
JWT_SECRET=local-dev-secret-key-change-this-min-32-chars-for-security
CORS_ORIGINS=http://localhost:5173
FRONTEND_URL=http://localhost:5173
BASE_URL=http://localhost:8000
```

**Frontend** (`frontend/.env.local`):

```bash
VITE_API_URL=http://localhost:8000
VITE_BROWSER_API_URL=http://localhost:8000
```

## Running the Application

### Option 1: VS Code Debugger (Recommended)

This is the **best way** to develop — full debugging with breakpoints!

1. Open the project in VS Code
2. Press **F5** (or click "Run and Debug" in sidebar)
3. Select **"Full Stack (Backend + Frontend)"**
4. Both servers start automatically
5. Set breakpoints anywhere and debug!

**Debugging Features:**

- Set breakpoints in Python code (backend)
- Inspect variables and call stack
- Step through code line by line
- Debug tests with breakpoints
- View console output in Debug Console

### Option 2: VS Code Tasks

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type **"Tasks: Run Task"**
3. Select **"Start Both Dev Servers"**

Both servers run in split terminal panels.

### Option 3: Manual Start (Terminal)

**Terminal 1 — Backend:**

```bash
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

## Accessing the Application

Once running, open your browser:

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **Alternative API Docs:** http://localhost:8000/redoc (ReDoc)

## Development Workflow

### Making Changes

**Backend (Python):**

1. Edit files in `backend/src/`
2. Server auto-reloads on save
3. Check terminal for any errors
4. Refresh browser to see API changes

**Frontend (HTML/JS/CSS):**

1. Edit files in `frontend/src/`
2. Browser auto-updates (Hot Module Replacement)
3. No manual refresh needed

### Running Tests

**Option 1: VS Code Test Explorer**

1. Open Testing sidebar (beaker icon)
2. Click "Run All Tests" or run individual tests
3. Set breakpoints in tests for debugging

**Option 2: VS Code Task**

1. `Ctrl+Shift+P` → "Tasks: Run Task"
2. Select "Run Backend Tests"

**Option 3: Terminal**

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

**Run specific test file:**

```bash
pytest tests/integration/test_auth.py -v
```

**Run with coverage:**

```bash
pytest --cov=src --cov-report=html
```

### Debugging Tests

1. Open test file in VS Code
2. Set breakpoints in test or source code
3. Press **F5** → Select **"Python: Pytest - Current File"**
4. Debugger stops at breakpoints during test execution

## Project Structure

```
vagrantfile-generator/
├── backend/
│   ├── .venv/              # Python virtual environment (local only)
│   ├── .env.local          # Local environment config (not committed)
│   ├── src/                # Source code
│   │   ├── main.py         # FastAPI application entry point
│   │   ├── api/            # API route handlers
│   │   ├── services/       # Business logic
│   │   ├── models/         # Data models
│   │   └── utils/          # Utilities
│   ├── tests/              # Tests
│   │   ├── integration/    # Integration tests
│   │   └── contract/       # Contract tests
│   ├── data/               # Runtime data (user projects, auth, etc.)
│   └── requirements.txt    # Python dependencies
│
├── frontend/
│   ├── node_modules/       # Node.js dependencies (local only)
│   ├── .env.local          # Local environment config (not committed)
│   ├── src/
│   │   ├── index.html      # Main HTML
│   │   ├── js/             # JavaScript modules
│   │   ├── components/     # Reusable components
│   │   ├── views/          # Page views
│   │   ├── modals/         # Modal dialogs
│   │   └── styles/         # CSS (Tailwind)
│   ├── package.json        # Node.js dependencies
│   └── vite.config.js      # Vite dev server config
│
├── .vscode/
│   ├── settings.json       # VS Code workspace settings
│   ├── launch.json         # Debug configurations
│   ├── tasks.json          # Task definitions
│   └── extensions.json     # Recommended extensions
│
└── setup-local-dev.sh      # Automated setup script
```

## VS Code Integration

### Recommended Extensions

The project includes `.vscode/extensions.json` with recommended extensions:

- **Python** — Python language support
- **Pylance** — Fast Python IntelliSense
- **Prettier** — Code formatting
- **Tailwind CSS IntelliSense** — Tailwind class autocomplete
- **GitLens** — Enhanced Git integration

VS Code will prompt to install these when you open the project.

### Keyboard Shortcuts

- **F5** — Start debugging
- **Ctrl+Shift+P** — Command Palette
- **Ctrl+`** — Toggle terminal
- **Ctrl+Shift+B** — Run build task
- **Ctrl+Shift+T** — Run test task

## Common Issues

### Port Already in Use

**Problem:** `Address already in use` error

**Solution:**

```bash
# Find process using port 8000 or 5173
lsof -i :8000
lsof -i :5173

# Kill the process
kill -9 <PID>
```

### Python Import Errors

**Problem:** `ModuleNotFoundError` when running backend

**Solution:**

1. Ensure virtual environment is activated:
   ```bash
   cd backend
   source .venv/bin/activate
   ```
2. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Check `PYTHONPATH` is set (should be automatic in VS Code)

### Frontend Not Loading

**Problem:** Blank page or errors in browser console

**Solution:**

1. Ensure backend is running (`curl http://localhost:8000/health`)
2. Check CORS settings in `backend/.env.local`
3. Verify `VITE_BROWSER_API_URL` in `frontend/.env.local`
4. Clear browser cache and hard refresh (Ctrl+Shift+R)

### CORS Errors

**Problem:** `Access to fetch blocked by CORS policy`

**Solution:**
Ensure `backend/.env.local` has:

```bash
CORS_ORIGINS=http://localhost:5173
```

Restart backend after changing.

### Dependencies Out of Date

**Problem:** Weird errors after pulling latest code

**Solution:**

```bash
# Backend
cd backend
source .venv/bin/activate
pip install -r requirements.txt --upgrade

# Frontend
cd frontend
npm install
```

## Switching Between Modes

### From Local Dev to Production Testing

1. Stop local dev servers (Ctrl+C or stop debugger)
2. Build and run production containers:
   ```bash
   make prod-up
   ```
3. Access at http://localhost:8080

### From Production Back to Local Dev

1. Stop production containers:
   ```bash
   make prod-down
   ```
2. Restart local development (F5 in VS Code)

## Performance Tips

**Backend:**

- Use `--reload` for development (already configured)
- Disable logging for better performance in `.env.local`: `LOG_LEVEL=WARNING`
- Use SQLite for tests (faster than file-based JSON)

**Frontend:**

- Vite is already optimized for dev
- Use browser DevTools Network tab to check API call times
- Consider using Redux DevTools for state debugging

## Data Directories

Local development uses the same data structure as containers:

```
backend/data/
├── auth/                   # Authentication data
│   ├── otp-requests.json   # OTP requests
│   └── rate-limits.json    # Rate limiting
├── shared/                 # Shared resources
│   ├── boxes/              # Vagrant boxes
│   ├── plugins/            # Vagrant plugins
│   ├── projects/           # Project templates
│   ├── provisioners/       # Provisioner templates
│   └── triggers/           # Trigger templates
└── users/                  # User-specific data
    └── <user-id>/          # Per-user storage
```

**Note:** `backend/data/users/` is gitignored — user data is never committed.

## Next Steps

- 📖 Read [ENVIRONMENTS.md](./ENVIRONMENTS.md) for production deployment
- 🧪 Check `backend/tests/` for test examples
- 📋 Review [CONTRIBUTING.md](../CONTRIBUTING.MD) for contribution guidelines
- 🏗️ See [APP_OVERVIEW.md](./APP_OVERVIEW.md) for architecture overview

## Need Help?

- Check API documentation: http://localhost:8000/docs (when running)
- Review existing code in `backend/src/api/` for examples
- Look at tests in `backend/tests/` for usage patterns
- Check GitHub Issues for known problems

Happy coding! 🚀
