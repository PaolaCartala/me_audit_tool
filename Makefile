# Makefile for em_audit_tool deployment

.PHONY: help dev prod setup-dev setup-prod deploy-dev deploy-prod

# Default target
help:
	@echo "Available commands:"
	@echo "  make dev         - Deploy to development environment"
	@echo "  make prod        - Deploy to production environment"
	@echo "  make setup-dev   - Setup development environment (.env)"
	@echo "  make setup-prod  - Setup production environment (.env)"

# Check if user is logged in to Azure
check-azure-login:
	@echo "Checking Azure login status..."
	@if ! az account show > /dev/null 2>&1; then \
		echo "Not logged in to Azure. Logging in..."; \
		az login; \
	else \
		echo "Already logged in to Azure."; \
	fi

# Setup development environment
setup-dev:
	@echo "Setting up development environment..."
	@cp .env.development .env
	@echo "Development environment configured."

# Setup production environment  
setup-prod:
	@echo "Setting up production environment..."
	@cp .env.production .env
	@echo "Production environment configured."

# Deploy to development
deploy-dev: check-azure-login setup-dev
	@echo "Deploying to development environment..."
	@echo "Restarting function app..."
	az functionapp restart --name audit-tool-dev --resource-group AppliedAI
	@echo "Publishing function app..."
	func azure functionapp publish audit-tool-dev --force
	@echo "Development deployment completed!"

# Deploy to production
deploy-prod: check-azure-login setup-prod
	@echo "Deploying to production environment..."
	@echo "Restarting function app..."
	az functionapp restart --name audit-tool --resource-group AppliedAI
	@echo "Publishing function app..."
	func azure functionapp publish audit-tool --force
	@echo "Production deployment completed!"

# Shorthand aliases
dev: deploy-dev
prod: deploy-prod
