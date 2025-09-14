# Orchestrator Platform - Deployment Makefile

.PHONY: help setup-pi setup-dev docker-build docker-up docker-down validate clean

# Default target
help:
	@echo "Orchestrator Platform Deployment Commands:"
	@echo ""
	@echo "  setup-pi      - Setup Raspberry Pi (run on target device)"
	@echo "  setup-dev     - Quick development setup"
	@echo "  docker-build  - Build Docker images"
	@echo "  docker-up     - Start Docker development environment"
	@echo "  docker-down   - Stop Docker development environment"
	@echo "  ansible-deploy- Deploy using Ansible"
	@echo "  validate      - Validate deployment"
	@echo "  clean         - Clean up temporary files"
	@echo ""

# Raspberry Pi setup
setup-pi:
	@echo "Setting up Raspberry Pi..."
	./setup_raspberry_pi.sh

# Development setup
setup-dev:
	@echo "Setting up development environment..."
	./quick_dev_setup.sh

# Docker commands
docker-build:
	@echo "Building Docker images..."
	cd docker && docker-compose build

docker-up:
	@echo "Starting Docker development environment..."
	cd docker && docker-compose up -d
	@echo "Services started. Access Node-RED at http://localhost:1880"

docker-down:
	@echo "Stopping Docker development environment..."
	cd docker && docker-compose down

docker-logs:
	@echo "Showing Docker logs..."
	cd docker && docker-compose logs -f

# Ansible deployment
ansible-deploy:
	@echo "Deploying with Ansible..."
	cd ansible && ansible-playbook -i inventory.yml orchestrator-playbook.yml

ansible-check:
	@echo "Checking Ansible deployment..."
	cd ansible && ansible-playbook -i inventory.yml orchestrator-playbook.yml --check

# Validation
validate:
	@echo "Validating deployment..."
	./validate_deployment.sh

# Cleanup
clean:
	@echo "Cleaning up temporary files..."
	rm -f *.log
	rm -f *.pid
	docker system prune -f || true

# Development helpers
dev-start:
	@echo "Starting development services..."
	cd .. && ./start_dev.sh

dev-stop:
	@echo "Stopping development services..."
	cd .. && ./stop_dev.sh

dev-test:
	@echo "Running development tests..."
	cd .. && ./test_dev.sh