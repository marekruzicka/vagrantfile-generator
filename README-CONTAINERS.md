# Vagrantfile Generator - Container Development Guide

This document provides comprehensive guidance for developing Vagrantfile Generator using containers. The application uses separate containers for the backend (Python/FastAPI) and frontend (Node.js/Vite) with hot reloading enabled for an optimal development experience.

## Prerequisites

- **Container Runtime**: Podman (recommended) or Docker installed
- **Compose Tool**: `podman-compose` (`pip install podman-compose`) or `docker-compose`
- **Make** (optional, for convenient commands)
- **Git** for version control

### System Requirements

- **CPU**: 2+ cores recommended
- **Memory**: 4GB+ RAM recommended
- **Storage**: 2GB+ free space
- **OS**: Linux, macOS, or Windows with WSL2

## Quick Start

### Option 1: Using Make Commands (Recommended)

```bash
# Start the development environment
make dev-setup

# View logs
make logs

# Stop services
make down

# Run tests
make test
```

### Option 2: Using podman-compose directly

```bash
# Build and start all services
podman-compose up --build -d

# View logs
podman-compose logs -f

# Stop services
podman-compose down
```

### Option 3: Using the test script

```bash
# Run comprehensive container tests
./test-containers.sh
```

## Services Overview

| Service  | URL                    | Description | Container |
|----------|------------------------|-------------|-----------|
| **Frontend** | http://localhost:5173  | Modern web interface with Vite dev server | `vagrantfile-gui-frontend` |
| **Backend**  | http://localhost:8000  | FastAPI application with auto-reload | `vagrantfile-gui-backend` |
| **API Docs** | http://localhost:8000/docs | Interactive Swagger/OpenAPI documentation | - |
| **Health**   | http://localhost:8000/health | Backend health check endpoint | - |

### Container Features

- **🔄 Hot Reloading**: Both frontend and backend automatically reload on code changes
- **📦 Volume Mounts**: Live code editing with immediate feedback
- **🗃️ Data Persistence**: Project data persists between container restarts
- **🏥 Health Checks**: Automatic service health monitoring
- **🔒 Network Isolation**: Services communicate through internal Docker network

## Available Commands

### Make Commands

- `make help` - Show all available commands
- `make build` - Build all containers
- `make up` - Start all services
- `make down` - Stop all services
- `make restart` - Restart all services
- `make logs` - Show logs from all services
- `make backend-logs` - Show backend logs only
- `make frontend-logs` - Show frontend logs only
- `make test` - Run all tests
- `make backend-test` - Run backend tests only
- `make clean` - Remove containers and volumes
- `make shell-backend` - Open shell in backend container
- `make shell-frontend` - Open shell in frontend container

### Direct Commands

```bash
# Start development environment
podman-compose up -d

# View logs
podman-compose logs -f

# Run backend tests
podman-compose exec backend python -m pytest tests/ -v

# Open shell in backend
podman-compose exec backend /bin/bash

# Open shell in frontend
podman-compose exec frontend /bin/sh

# Stop and remove everything
podman-compose down -v
```

## Development Workflow

1. **Start the environment:**
   ```bash
   make dev-setup
   ```

2. **Develop your code:**
   - Backend code in `./backend/` (auto-reloads)
   - Frontend code in `./frontend/` (auto-reloads)

3. **Run tests:**
   ```bash
   make test
   # or for comprehensive testing
   ./test-containers.sh
   ```

4. **View logs when debugging:**
   ```bash
   make logs
   # or specific service
   make backend-logs
   ```

5. **Stop when done:**
   ```bash
   make down
   ```

## Container Architecture

### Backend Container (`vagrantfile-gui-backend`)
- **Base Image**: Python 3.11 slim
- **Port**: 8000 (mapped to host:8000)
- **Volume**: `./backend:/app` (live code reload)
- **Data Volume**: `backend-data` (persistent project storage)
- **Health Check**: `/health` endpoint monitoring
- **Auto-reload**: Uvicorn watches for Python file changes
- **Dependencies**: Installed via `requirements.txt` during build

### Frontend Container (`vagrantfile-gui-frontend`)
- **Base Image**: Node.js 18 Alpine
- **Port**: 5173 (mapped to host:5173)
- **Volume**: `./frontend:/app` (live code reload)
- **Build Process**: Automatic Tailwind CSS compilation
- **Health Check**: HTTP request to Vite dev server
- **Hot Module Replacement**: Instant UI updates on file changes
- **Dependencies**: Installed via `package.json` during build

### Network Architecture
```
Host Machine
├── localhost:5173 → Frontend Container (Vite)
├── localhost:8000 → Backend Container (FastAPI)
└── Internal Network
    ├── frontend → backend:8000 (API calls)
    └── backend-data (persistent volume)
```

## Testing Strategies

The project includes comprehensive testing approaches for containerized development:

### 1. Backend Unit & Integration Tests
```bash
# Run all backend tests
make backend-test

# Run specific test categories
podman-compose exec backend python -m pytest tests/unit/ -v
podman-compose exec backend python -m pytest tests/integration/ -v
podman-compose exec backend python -m pytest tests/contract/ -v
```

### 2. Container Integration Testing
```bash
# Comprehensive container testing
./test-containers.sh

# Custom container tests
podman-compose exec backend curl -f http://localhost:8000/health
podman-compose exec frontend wget --spider http://localhost:5173
```

### 3. End-to-End Workflow Testing
```bash
# Test complete application workflow
make test

# Manual testing workflow:
# 1. Open http://localhost:5173
# 2. Create a new project
# 3. Add a VM configuration
# 4. Generate Vagrantfile
# 5. Verify API calls in http://localhost:8000/docs
```

### 4. Performance Testing
```bash
# Check container resource usage
podman stats

# Monitor logs for performance issues
make logs

# Test API response times
curl -w "%{time_total}\n" http://localhost:8000/api/projects
```

## Troubleshooting

### Common Issues and Solutions

#### Container won't start
```bash
# Check container logs for errors
make logs

# Check specific service logs
make backend-logs
make frontend-logs

# Rebuild containers from scratch
make clean
make build
make up
```

#### Port conflicts
If ports 5173 or 8000 are already in use:

1. **Check what's using the ports:**
   ```bash
   # Linux/macOS
   lsof -i :5173
   lsof -i :8000
   
   # Windows
   netstat -ano | findstr :5173
   netstat -ano | findstr :8000
   ```

2. **Modify `docker-compose.yml`:**
   ```yaml
   services:
     frontend:
       ports:
         - "5174:5173"  # Use port 5174 instead
     backend:
       ports:
         - "8001:8000"  # Use port 8001 instead
   ```

#### CSS not loading / Styling issues
```bash
# Rebuild frontend with fresh CSS compilation
podman-compose exec frontend npm run tailwind

# Or rebuild the entire frontend container
podman-compose down
podman-compose up --build frontend
```

#### Permission issues (Linux/macOS)
```bash
# Fix file ownership
sudo chown -R $USER:$USER ./backend ./frontend

# Fix directory permissions
chmod -R 755 ./backend ./frontend
```

#### Database/Data issues
```bash
# Reset all data (WARNING: This deletes all projects)
podman-compose down -v

# Backup data before reset
podman cp vagrantfile-gui-backend:/app/data ./backup-data
```

#### Memory/Performance issues
```bash
# Check container resource usage
podman stats

# Increase container memory limits in docker-compose.yml
# Add under each service:
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
```

#### Network connectivity issues
```bash
# Test internal network connectivity
podman-compose exec frontend curl http://backend:8000/health

# Check network configuration
podman network ls
podman network inspect vagrantfile-gui-network
```

### Clean Slate Recovery
When all else fails, start completely fresh:

```bash
# Stop and remove everything
make clean

# Remove any orphaned containers
podman container prune -f

# Remove any orphaned volumes
podman volume prune -f

# Remove any orphaned networks
podman network prune -f

# Start fresh
make dev-setup
```

## Data Persistence

### Project Data Storage
- **Location**: Named volume `backend-data` mounted at `/app/data`
- **Contents**: All project configurations and metadata stored as JSON files
- **Persistence**: Data survives container restarts and updates
- **Backup**: Regular backups recommended for production use

### Volume Management
```bash
# List all volumes
podman volume ls

# Inspect backend data volume
podman volume inspect vagrantfile-generator_backend-data

# Backup project data
podman cp vagrantfile-gui-backend:/app/data ./project-backup

# Restore project data
podman cp ./project-backup/. vagrantfile-gui-backend:/app/data/

# Reset all data (WARNING: Irreversible)
podman-compose down -v
```

### Development Data Workflow
1. **Development**: Data persists during `make restart` and `make up/down`
2. **Updates**: Data preserved during container rebuilds (`make build`)
3. **Clean**: Data removed only with `make clean` or `podman-compose down -v`
4. **Backup**: Manual backup before major changes recommended

## Hot Reloading

Both services support hot reloading:
- **Backend:** Uvicorn auto-reloads on Python file changes
- **Frontend:** Vite auto-reloads on HTML/CSS/JS file changes
- **Tailwind:** CSS rebuilds automatically during development

## Production Notes

For production deployment:
1. Set `NODE_ENV=production` for frontend
2. Set `ENVIRONMENT=production` for backend
3. Use `vite build` for frontend static assets
4. Consider using nginx for frontend serving
5. Use proper secrets management for production