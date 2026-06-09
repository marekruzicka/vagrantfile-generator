# Quick Reference - Development Commands

## First Time Setup

```bash
./setup-local-dev.sh
```

## Daily Development

### Start Application

| Method               | Command                                                   | Best For                          |
| -------------------- | --------------------------------------------------------- | --------------------------------- |
| **VS Code Debugger** | Press `F5`                                                | Active debugging with breakpoints |
| **VS Code Tasks**    | `Ctrl+Shift+P` → Tasks: Run Task → Start Both Dev Servers | Background running                |
| **Manual**           | See below                                                 | Terminal workflow                 |

**Manual Start:**

```bash
# Terminal 1
cd backend && source .venv/bin/activate && uvicorn src.main:app --reload

# Terminal 2
cd frontend && npm run dev
```

**URLs:**

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Run Tests

```bash
# All tests
cd backend && source .venv/bin/activate && pytest tests/ -v

# Specific test file
pytest tests/integration/test_auth.py -v

# With coverage
pytest --cov=src --cov-report=html

# In VS Code: Press F5 → "Python: Pytest - All Tests"
```

### Update Dependencies

```bash
# Backend
cd backend && source .venv/bin/activate && pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

## Production Testing

```bash
# Build and run production containers
make prod-up

# View logs
make prod-logs

# Stop
make prod-down

# Clean everything
make prod-clean
```

**URL:** http://localhost:8080

## User Distribution Mode

```bash
# Start with prebuilt images
make user-up

# Stop
make user-down

# View logs
make user-logs
```

## VS Code Shortcuts

| Shortcut       | Action            |
| -------------- | ----------------- |
| `F5`           | Start debugging   |
| `Ctrl+Shift+P` | Command palette   |
| `Ctrl+``       | Toggle terminal   |
| `F9`           | Toggle breakpoint |
| `F10`          | Step over         |
| `F11`          | Step into         |
| `Shift+F11`    | Step out          |
| `Shift+F5`     | Stop debugging    |

## Common Tasks

### Add Python Dependency

```bash
cd backend
source .venv/bin/activate
pip install <package>
pip freeze > requirements.txt
```

### Add Frontend Dependency

```bash
cd frontend
npm install <package>
# package.json updated automatically
```

### Rebuild Tailwind CSS

```bash
cd frontend
npm run tailwind

# Or watch mode
npm run tailwind:watch
```

### Check for Errors

```bash
# Backend
cd backend && source .venv/bin/activate
python -m pylint src/
python -m mypy src/

# Frontend
cd frontend
npm run build  # Check for build errors
```

## Debugging Tips

### Backend (Python)

1. Set breakpoint: Click left of line number in VS Code
2. Press F5 → "Python: FastAPI Backend"
3. Make API request from browser/frontend
4. Debugger stops at breakpoint

### Tests

1. Open test file
2. Set breakpoint in test or source code
3. Press F5 → "Python: Pytest - Current File"
4. Step through with F10/F11

### Frontend (Browser)

1. Open browser DevTools (F12)
2. Use Console tab for logs
3. Use Network tab for API calls
4. Use Elements tab for DOM inspection

## Troubleshooting

### Port in Use

```bash
# Find process
lsof -i :8000
lsof -i :5173

# Kill process
kill -9 <PID>
```

### Module Not Found

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

### CORS Error

Check `backend/.env.local`:

```bash
CORS_ORIGINS=http://localhost:5173
```

### Can't Debug

Check `.vscode/launch.json` exists and VS Code Python extension is installed.

## Environment Files

### Backend: `backend/.env.local`

```bash
DEPLOYMENT_MODE=self-hosted
CORS_ORIGINS=http://localhost:5173
FRONTEND_URL=http://localhost:5173
BASE_URL=http://localhost:8000
```

### Frontend: `frontend/.env.local`

```bash
VITE_API_URL=http://localhost:8000
VITE_BROWSER_API_URL=http://localhost:8000
```

## When to Use Each Mode

| Mode                | Use When                                   |
| ------------------- | ------------------------------------------ |
| **DEV (local)**     | Writing code, debugging, running tests     |
| **PROD (build)**    | Testing production config, smoke testing   |
| **USER (prebuilt)** | Deploying to server, end-user distribution |

## Get Help

- **Documentation**: `docs/LOCAL_DEVELOPMENT.md`
- **Environments**: `docs/ENVIRONMENTS.md`
- **Makefile**: Run `make help`
- **API Docs**: http://localhost:8000/docs (when running)
