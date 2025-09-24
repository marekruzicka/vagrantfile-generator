# Vagrantfile Generator - Development with Podman
# 
# This Makefile provides convenient commands for development using Podman containers

.PHONY: help build up down logs clean test backend-test restart backend-logs frontend-logs

# Default target
help:
	@echo "Vagrantfile Generator - Podman Development Commands"
	@echo "======================================================="
	@echo ""
	@echo "Commands:"
	@echo "  make build          - Build all containers"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - Show logs from all services"
	@echo "  make backend-logs   - Show backend logs"
	@echo "  make frontend-logs  - Show frontend logs"
	@echo "  make clean          - Remove containers and volumes"
	@echo "  make test           - Run all tests"
	@echo "  make backend-test   - Run backend tests"
	@echo ""
	@echo "Configuration:"
	@echo "  Dev (default): Defaults to localhost"
	@echo "  Prod: Set CORS_ORIGINS and VITE_API_URL environment variables"
	@echo ""
	@echo "URLs:"
	@echo "  Frontend: http://localhost:5173"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

# Build all containers
build:
	podman-compose build

# Start all services
up:
	podman-compose up -d

# Stop all services
down:
	podman-compose down

# Restart services
restart: down up

# Show logs from all services
logs:
	podman-compose logs -f

# Show backend logs
backend-logs:
	podman-compose logs backend

# Show frontend logs
frontend-logs:
	podman-compose logs frontend

# Run all tests
test: backend-test

# Run backend tests
backend-test:
	podman-compose exec backend python -m pytest tests/ -v

# Clean up containers and volumes
clean:
	podman-compose down -v
	podman system prune -f