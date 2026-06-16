# Vagrantfile Generator - Compose Development Commands
#
# This Makefile provides developer-only convenience commands for local
# container builds and smoke tests via compose-dev.yml.

.PHONY: help setup-local build up down restart logs backend-logs frontend-logs clean

# Include Helm workflow (helm-package, helm-push, helm-release, etc.)
include helm.mk

COMPOSE ?= $(shell command -v podman-compose >/dev/null 2>&1 && echo podman-compose || echo "docker compose")

# Default target
help:
	@echo "Vagrantfile Generator - Development Commands"
	@echo "============================================="
	@echo ""
	@echo "NATIVE DEVELOPMENT (no containers):"
	@echo "  make setup-local    - Set up local development environment"
	@echo "  After setup, use VS Code tasks or debugger to run the app"
	@echo ""
	@echo "COMPOSE DEV BUILD (compose-dev.yml):"
	@echo "  make build          - Build local images without cache"
	@echo "  make up             - Start local-build stack"
	@echo "  make down           - Stop local-build stack"
	@echo "  make restart        - Restart local-build stack"
	@echo "  make logs           - Follow logs from local-build stack"
	@echo "  make backend-logs   - Follow backend logs"
	@echo "  make frontend-logs  - Follow frontend logs"
	@echo "  make clean          - Stop stack and remove volumes"
	@echo ""
	@echo "Native development URLs:"
	@echo "  Frontend: http://localhost:5173"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "Compose dev URLs:"
	@echo "  Frontend: http://localhost:8080"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API:      http://localhost:8080/api"

# =============================================================================
# NATIVE DEVELOPMENT (runs outside containers)
# =============================================================================

setup-local:
	@echo "Setting up local development environment..."
	./setup-local-dev.sh

# =============================================================================
# COMPOSE DEV BUILD (compose-dev.yml - local builds for smoke testing)
# =============================================================================

build:
	$(COMPOSE) -f compose-dev.yml build --no-cache

up:
	$(COMPOSE) -f compose-dev.yml up -d --build

down:
	$(COMPOSE) -f compose-dev.yml down

restart: down up

logs:
	$(COMPOSE) -f compose-dev.yml logs -f

backend-logs:
	$(COMPOSE) -f compose-dev.yml logs -f backend

frontend-logs:
	$(COMPOSE) -f compose-dev.yml logs -f frontend

clean:
	$(COMPOSE) -f compose-dev.yml down -v
