.PHONY: help install dev backend frontend seed clean check test build

help: ## Show this help message
	@echo "L'Aura Project - Available Commands"
	@echo "===================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

check: ## Check if all dependencies are installed
	@python3 scripts/check-deps.py

install: ## Install all dependencies (backend + frontend)
	@echo "📦 Installing dependencies..."
	@cd backend && pip install -r requirements.txt
	@cd frontend && yarn install
	@echo "✅ Dependencies installed!"

seed: ## Seed database with initial data
	@echo "🌱 Seeding database..."
	@cd backend && python seed.py
	@echo "✅ Database seeded!"

setup: check install seed ## Complete setup (check + install + seed)
	@echo ""
	@echo "✅ Setup complete!"
	@echo "📝 Run 'make dev' to start development servers"

dev: ## Start both backend and frontend (requires 2 terminals)
	@echo "🚀 Starting development servers..."
	@echo "   Terminal 1: Backend (port 8001)"
	@echo "   Terminal 2: Frontend (port 3000)"
	@echo ""
	@echo "Run in separate terminals:"
	@echo "   make backend"
	@echo "   make frontend"

backend: ## Start backend only
	@echo "🔧 Starting backend on http://localhost:8001"
	@cd backend && uvicorn server:app --host 0.0.0.0 --port 8001 --reload

frontend: ## Start frontend only
	@echo "🎨 Starting frontend on http://localhost:3000"
	@cd frontend && yarn start

build: ## Build for production
	@echo "🏗️  Building for production..."
	@cd frontend && yarn build
	@echo "✅ Production build complete! (frontend/build/)"

test-backend: ## Test backend health
	@echo "🧪 Testing backend..."
	@curl -f http://localhost:8001/api/health || echo "❌ Backend not running"

test-frontend: ## Test frontend build
	@echo "🧪 Testing frontend build..."
	@cd frontend && CI=true yarn build

test: test-backend ## Run all tests

clean: ## Clean build artifacts and caches
	@echo "🧹 Cleaning..."
	@rm -rf frontend/build
	@rm -rf frontend/node_modules
	@rm -rf backend/__pycache__
	@rm -rf backend/.pytest_cache
	@echo "✅ Clean complete!"

logs: ## Show supervisor logs
	@tail -f /var/log/supervisor/backend.out.log /var/log/supervisor/frontend.out.log

restart: ## Restart all services (supervisor)
	@sudo supervisorctl restart all
	@sudo supervisorctl status
