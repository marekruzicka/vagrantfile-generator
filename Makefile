# Vagrantfile Generator - Development with Podman
# 
# This Makefile provides convenient commands for development using Podman containers

.PHONY: help dev build up down logs clean restart backend-logs frontend-logs

# Default target
help:
	@echo "Vagrantfile Generator - Podman Development Commands"
	@echo "======================================================="
	@echo ""
	@echo "Commands:"
	@echo "	 make dev						 - Build and run all containers"
	@echo "  make build          - Build all containers"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - Show logs from all services"
	@echo "  make backend-logs   - Show backend logs"
	@echo "  make frontend-logs  - Show frontend logs"
	@echo "  make clean          - Remove containers and volumes"
	@echo ""
	@echo "Configuration"
	@echo "URLs:"
	@echo "  Frontend: http://localhost:5173"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

# Build and run all containers
dev:
	podman-compose -f docker-compose-dev.yml up -d --build

# Build all containers
build:
	podman-compose -f docker-compose-dev.yml build

# Start all services
up:
	podman-compose -f docker-compose-dev.yml up -d

# Stop all services
down:
	podman-compose -f docker-compose-dev.yml down

# Restart services
restart: down up

# Show logs from all services
logs:
	podman-compose -f docker-compose-dev.yml logs

# Show backend logs
backend-logs:
	podman-compose -f docker-compose-dev.yml logs backend

# Show frontend logs
frontend-logs:
	podman-compose -f docker-compose-dev.yml logs frontend

# Clean up containers and volumes
clean:
	podman-compose -f docker-compose-dev.yml down -v
	podman system prune -f
