# Vagrantfile Generator - Podman Compose Commands
# 
# This Makefile provides convenient commands for running containerized environments

.PHONY: help setup-local build up down restart logs backend-logs frontend-logs clean user-up user-down user-logs user-clean

# Default target
help:
	@echo "Vagrantfile Generator - Environment Commands"
	@echo "=============================================="
	@echo ""
	@echo "LOCAL DEVELOPMENT (no containers):"
	@echo "  make setup-local         - Set up local development environment"
	@echo "  After setup, use VS Code tasks or debugger to run the app"
	@echo ""
	@echo "PRODUCTION BUILD (local build for testing):"
	@echo "  make build          - Build production images locally"
	@echo "  make up             			- Start production-like stack"
	@echo "  make down           			- Stop production stack"
	@echo "  make restart			        - Restart production stack"
	@echo "  make logs           - Show logs from production stack"
	@echo "  make backend-logs   - Show backend logs (production)"
	@echo "  make frontend-logs  - Show frontend logs (production)"
	@echo "  make clean          - Clean production containers and volumes"
	@echo ""
	@echo "USER DISTRIBUTION (prebuilt images):"
	@echo "  make user-up             - Start using prebuilt images"
	@echo "  make user-down           - Stop user environment"
	@echo "  make user-logs           - Show logs from user environment"
	@echo "  make user-clean          - Clean user containers and volumes"
	@echo ""
	@echo "Development URLs (local):"
	@echo "  Frontend: http://localhost:5173"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "Production URLs (containerized):"
	@echo "  Frontend: http://localhost:8080"
	@echo "  Backend:  http://localhost:8000 (internal)"
	@echo "  API:      http://localhost:8080/api"

# =============================================================================
# LOCAL DEVELOPMENT (runs outside containers)
# =============================================================================

setup-local:
	@echo "Setting up local development environment..."
	./setup-local-dev.sh

# =============================================================================
# PRODUCTION BUILD (compose-prod.yml - local builds for testing)
# =============================================================================

build:
	podman-compose -f compose-prod.yml build --no-cache

up:
	podman-compose -f compose-prod.yml up -d --build

down:
	podman-compose -f compose-prod.yml down -v


restart: down up

logs:
	podman-compose -f compose-prod.yml logs

backend-logs:
	podman-compose -f compose-prod.yml logs backend

frontend-logs:
	podman-compose -f compose-prod.yml logs frontend

clean:
	podman-compose -f compose-prod.yml down -v
	podman system prune -f

# =============================================================================
# USER DISTRIBUTION (compose.yml - prebuilt images)
# =============================================================================

user-up:
	podman-compose up -d

user-down:
	podman-compose down

user-logs:
	podman-compose logs

user-clean:
	podman-compose down -v
	podman system prune -f
