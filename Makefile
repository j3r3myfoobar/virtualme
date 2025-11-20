.PHONY: help install test clean localstack-up localstack-down localstack-deploy aws-deploy aws-destroy

# Default target
help:
	@echo "Virtual Me Chatbot - Makefile Commands"
	@echo "======================================"
	@echo ""
	@echo "Local Development (LocalStack):"
	@echo "  make install           - Install Python dependencies"
	@echo "  make localstack-up     - Start LocalStack container"
	@echo "  make localstack-deploy - Deploy to LocalStack"
	@echo "  make localstack-down   - Stop LocalStack container"
	@echo "  make test-local        - Test Lambda function locally"
	@echo ""
	@echo "AWS Production:"
	@echo "  make aws-deploy        - Deploy to AWS using Terraform"
	@echo "  make aws-plan          - Show Terraform deployment plan"
	@echo "  make aws-destroy       - Destroy AWS infrastructure"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean             - Remove build artifacts"
	@echo "  make validate          - Validate all configurations"
	@echo ""

# Install Python dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt

# Start LocalStack
localstack-up:
	@echo "Starting LocalStack..."
	docker-compose up -d
	@echo "Waiting for LocalStack to be ready..."
	@sleep 5
	@echo "LocalStack is ready!"

# Deploy to LocalStack
localstack-deploy: localstack-up
	@echo "Deploying to LocalStack..."
	@chmod +x localstack-deploy.sh
	@./localstack-deploy.sh

# Stop LocalStack
localstack-down:
	@echo "Stopping LocalStack..."
	docker-compose down

# Test Lambda locally
test-local:
	@echo "Testing Lambda function locally..."
	@export OPENAI_API_KEY="${OPENAI_API_KEY}" && python lambda_function.py

# Terraform plan
aws-plan:
	@echo "Creating Terraform plan..."
	@cd terraform && terraform init && terraform plan

# Deploy to AWS
aws-deploy:
	@echo "Deploying to AWS..."
	@cd terraform && chmod +x deploy.sh && ./deploy.sh

# Destroy AWS infrastructure
aws-destroy:
	@echo "WARNING: This will destroy all AWS resources!"
	@read -p "Are you sure? Type 'yes' to continue: " confirm && \
	if [ "$$confirm" = "yes" ]; then \
		cd terraform && terraform destroy; \
	else \
		echo "Cancelled."; \
	fi

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf package/
	rm -f deployment.zip
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -f response.json
	rm -f output.json
	@echo "Clean complete!"

# Validate configurations
validate:
	@echo "Validating configurations..."
	@echo "✓ Checking Python syntax..."
	@python -m py_compile lambda_function.py
	@echo "✓ Checking Terraform configuration..."
	@cd terraform && terraform fmt -check && terraform validate
	@echo "✓ All validations passed!"

# Create deployment package (without deploying)
package:
	@echo "Creating deployment package..."
	@rm -rf package deployment.zip
	@mkdir -p package
	@pip install -r requirements.txt -t package/ --quiet
	@cp lambda_function.py package/
	@cp resume.md package/
	@cd package && zip -q -r ../deployment.zip .
	@echo "✓ Package created: deployment.zip"

# View LocalStack logs
localstack-logs:
	@docker logs -f virtualme-localstack

# Run all checks before deployment
pre-deploy: clean validate
	@echo "✓ Pre-deployment checks passed!"
