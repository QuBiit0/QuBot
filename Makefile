# Qubot Makefile

.PHONY: help install dev test build deploy clean

# Default target
help:
	@echo "Qubot Development Commands"
	@echo "=========================="
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install all dependencies"
	@echo "  make install-backend  Install backend dependencies"
	@echo "  make install-frontend Install frontend dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev              Start development environment"
	@echo "  make dev-backend      Start backend in dev mode"
	@echo "  make dev-frontend     Start frontend in dev mode"
	@echo "  make worker           Start worker process"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-backend     Run backend tests"
	@echo "  make coverage         Run tests with coverage"
	@echo ""
	@echo "Build:"
	@echo "  make build            Build all Docker images"
	@echo "  make build-backend    Build backend image"
	@echo "  make build-frontend   Build frontend image"
	@echo ""
	@echo "Deploy:"
	@echo "  make deploy           Deploy to Kubernetes"
	@echo "  make deploy-local     Deploy locally with Docker Compose"
	@echo "  make undeploy         Remove deployment"
	@echo ""
	@echo "Maintenance:"
	@echo "  make migrate          Run database migrations"
	@echo "  make seed             Seed database"
	@echo "  make clean            Clean up containers and volumes"
	@echo "  make logs             View logs"

# Setup
install: install-backend install-frontend

install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

# Development
dev:
	docker-compose up -d db redis
	@echo "Waiting for database..."
	@sleep 5
	make -j2 dev-backend dev-frontend

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

worker:
	cd backend && python -m app.worker

# Testing
test: test-backend

test-backend:
	cd backend && pytest tests/ -v

test-frontend:
	cd frontend && npm test

coverage:
	cd backend && pytest tests/ --cov=app --cov-report=html

# Build
build: build-backend build-frontend

build-backend:
	docker build -t qubot/api:latest -f backend/Dockerfile ./backend
	
build-worker:
	docker build -t qubot/worker:latest -f backend/Dockerfile.worker ./backend

build-frontend:
	docker build -t qubot/frontend:latest ./frontend

# Deployment
deploy-local:
	docker-compose up -d

deploy:
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/secrets.yaml
	kubectl apply -f k8s/api-deployment.yaml
	kubectl apply -f k8s/worker-deployment.yaml
	kubectl apply -f k8s/ingress.yaml

undeploy:
	kubectl delete -f k8s/ --ignore-not-found=true

# Maintenance
migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -c "from scripts.seed_db import seed; seed()"

clean:
	docker-compose down -v
	docker system prune -f

logs:
	docker-compose logs -f

logs-api:
	kubectl logs -f deployment/qubot-api -n qubot

logs-worker:
	kubectl logs -f deployment/qubot-worker -n qubot

# Database
db-reset:
	docker-compose down -v
	docker-compose up -d db
	@sleep 5
	make migrate
	make seed

# Utilities
format:
	cd backend && black app/ tests/
	cd frontend && npm run lint -- --fix

lint:
	cd backend && flake8 app/ tests/
	cd frontend && npm run lint

shell:
	docker-compose exec api bash

# Production helpers
prod-logs:
	kubectl logs -f deployment/qubot-api -n qubot --all-containers=true

prod-scale-api:
	kubectl scale deployment qubot-api --replicas=$(REPLICAS) -n qubot

prod-scale-worker:
	kubectl scale deployment qubot-worker --replicas=$(REPLICAS) -n qubot

prod-status:
	kubectl get pods -n qubot
	kubectl get svc -n qubot
	kubectl get ingress -n qubot
