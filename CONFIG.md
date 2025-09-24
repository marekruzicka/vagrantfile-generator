# Configuration Guide

## Simple Two-Environment Setup

### Development (Default)
- Default configuration in docker-compose.yml
- Supports localhost access only (minimal secure config)
- Run: `make build && make up`

### Production  
Edit docker-compose.yml environment variables:
```yaml
environment:
  - CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
  - VITE_API_URL=https://api.yourdomain.com
  - VITE_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,1.2.3.4
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated list of allowed origins |
| `VITE_API_URL` | `http://localhost:8000` | Backend API URL for frontend |
| `VITE_ALLOWED_HOSTS` | `localhost` | Comma-separated list of additional allowed hosts (localhost,127.0.0.1 always included in code) |

## Configuration Examples

### Development with Additional Hosts
To add more hosts for development (e.g., k8plus, container IPs):
```yaml
# In docker-compose.yml backend service:
- CORS_ORIGINS=http://localhost:5173,http://k8plus:5173

# In docker-compose.yml frontend service:
- VITE_ALLOWED_HOSTS=localhost,k8plus,10.89.0.3,.local
```

### Production Configuration
```yaml
# Backend environment:
- CORS_ORIGINS=https://app.yourdomain.com,https://www.yourdomain.com
- VITE_API_URL=https://api.yourdomain.com

# Frontend environment:
- VITE_ALLOWED_HOSTS=app.yourdomain.com,www.yourdomain.com,staging.yourdomain.com
```

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