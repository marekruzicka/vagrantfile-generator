# Vagrantfile Generator - Development with Podman
# 
# This Makefile provides convenient commands for development using Podman containers

.PHONY: help build up down logs clean test backend-test frontend-test restart

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
	@echo "  make test           - Run all tests"
	@echo "  make backend-test   - Run backend tests"
	@echo "  make clean          - Remove containers and volumes"
	@echo "  make shell-backend  - Open shell in backend container"
	@echo "  make shell-frontend - Open shell in frontend container"
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
	podman-compose logs -f backend

# Show frontend logs
frontend-logs:
	podman-compose logs -f frontend

# Run all tests
test: backend-test

# Run backend tests
backend-test:
	podman-compose exec backend python -m pytest tests/ -v

# Run frontend tests (when we add them)
frontend-test:
	@echo "Frontend tests not implemented yet"

# Clean up containers and volumes
clean:
	podman-compose down -v
	podman system prune -f

# Open shell in backend container
shell-backend:
	podman-compose exec backend /bin/bash

# Open shell in frontend container
shell-frontend:
	podman-compose exec frontend /bin/sh

# Development workflow commands
dev-setup: build up
	@echo "Development environment started!"
	@echo "Frontend: http://localhost:5173"
	@echo "Backend: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

# Quick restart for development
dev-restart:
	podman-compose restart backend frontend