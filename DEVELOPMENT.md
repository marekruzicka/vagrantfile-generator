# Development Guide

This document provides guidance for developing Vagrantfile Generator. The application uses separate containers for the backend (Python/FastAPI) and frontend (Node.js/Vite) with hot reloading enabled for an optimal development experience.

## Prerequisites

- **Container Runtime**: Podman (recommended) or Docker installed
- **Compose Tool**: `podman-compose` (`pip install podman-compose`) or `docker-compose`
- **Make** (wrapper around podman/docker)
Note that development version of frontend uses `Dockerfile-dev` and also `docker-compose-dev.yml`. Makefile wraps this up, for convenience.
- **Git** for version control

### System Requirements

- **CPU**: 2+ cores recommended
- **Memory**: 4GB+ RAM recommended
- **Storage**: 2GB+ free space
- **OS**: Linux, macOS, or Windows with WSL2

## Quick Start

### Option 1: Using Make Commands (Recommended)

```bash
# Build container images
make build

# Start the development environment
make up

# View logs
make logs

# Restart services when needed
make restart

# Stop services
make down

# Clean everything (containers, volumes, and unused images)
make clean
```

### Option 2: Using podman-compose directly

```bash
# Build and start all services
podman-compose -f docker-compose-dev.yml up --build -d

# View logs
podman-compose -f docker-compose-dev.yml logs -f

# Stop services
podman-compose -f docker-compose-dev.yml down
```

## Services Overview

| Service  | URL                    | Description | Container |
|----------|------------------------|-------------|-----------|
| **Frontend** | http://localhost:5173  | Modern web interface with Vite dev server | `vagrantfile-frontend` |
| **Backend**  | http://localhost:8000  | FastAPI application with auto-reload | `vagrantfile-backend` |
| **API Docs** | http://localhost:8000/docs | Interactive Swagger/OpenAPI documentation | - |
| **Health**   | http://localhost:8000/health | Backend health check endpoint | - |

### Container Features

- **🔄 Hot Reloading**: Both frontend and backend automatically reload on code changes
- **📦 Volume Mounts**: Live code editing with immediate feedback
- **🗃️ Data Persistence**: Project data persists between container restarts
- **🔒 Network Isolation**: Services communicate through internal Docker network

## Available Commands

### Make Commands

- `make help` - Show all available commands
- `make dev` - One liner to build and run
- `make build` - Build all containers
- `make up` - Start all services
- `make down` - Stop all services
- `make restart` - Restart all services
- `make logs` - Show logs from all services
- `make backend-logs` - Show backend logs only
- `make frontend-logs` - Show frontend logs only
- `make clean` - Remove containers, volumes, and prune unused Podman resources


## Development Workflow

1. **Start the environment:**
   ```bash
   make dev
   ```

2. **Develop your code:**
   - Backend code in `./backend/` (auto-reloads)
   - Frontend code in `./frontend/` (auto-reloads)

3. **View logs when debugging:**
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

### Backend Container (`vagrantfile-gen-backend`)
- **Base Image**: Python 3.11 slim
- **Port**: 8000 (mapped to host:8000)
- **Volumes**: `./backend:/app` (live code reload) and `./backend/data:/app/data` (project storage)
- **Health Check**: `/health` endpoint monitoring
- **Auto-reload**: Uvicorn watches for Python file changes
- **Dependencies**: Installed via `requirements.txt` during build

### Frontend Container (`vagrantfile-gen-frontend`)
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
```

## Data Persistence

### Project Data Storage
- **Location**: Host directory `./backend/data` mounted inside the backend container at `/app/data`
- **Contents**: All project configurations and metadata stored as JSON files
- **Persistence**: Data survives container restarts and rebuilds because it lives in the repository
- **Backup**: Commit to version control or copy `backend/data/` elsewhere before major changes

## Hot Reloading

Both services support hot reloading:
- **Backend:** Uvicorn auto-reloads on Python file changes
- **Frontend:** Vite auto-reloads on HTML/CSS/JS file changes
- **Tailwind:** CSS rebuilds automatically during development
