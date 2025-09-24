# Configuration Guide

## Simple Two-Environment Setup

### Development (Default)
- No configuration needed
- Defaults to `localhost` for both frontend and backend
- Run: `make build && make up`

### Production  
Set environment variables:
```bash
export CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
export VITE_API_URL="https://api.yourdomain.com" 
make build && make up
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated list of allowed origins |
| `VITE_API_URL` | `http://localhost:8000` | Backend API URL for frontend |

## Make Commands

| Command | Description |
|---------|-------------|
| `make build` | Build all containers |
| `make up` | Start all services |
| `make down` | Stop all services |
| `make restart` | Restart all services |
| `make logs` | Show logs from all services |
| `make backend-logs` | Show backend logs |
| `make frontend-logs` | Show frontend logs |
| `make clean` | Remove containers and volumes |
| `make test` | Run all tests |
| `make backend-test` | Run backend tests |

## Access URLs

- Frontend: http://localhost:5173
- Backend: http://localhost:8000  
- API Docs: http://localhost:8000/docs