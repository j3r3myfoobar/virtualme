# Command Reference

This project uses **bash scripts** for all deployment and testing operations. No Makefile required!

## 📋 Quick Reference

### Local Testing

```bash
# Quick start (installs deps and tests)
./scripts/quickstart.sh

# Test Lambda function locally
export OPENAI_API_KEY="sk-proj-xxx"
cd src && python lambda_function.py
```

### LocalStack (Local Development)

```bash
# Start LocalStack
docker-compose up -d

# Deploy to LocalStack
export OPENAI_API_KEY="sk-proj-xxx"
./scripts/localstack-deploy.sh

# View logs
docker logs -f virtualme-localstack

# Stop LocalStack
docker-compose down
```

### AWS Production

```bash
# Option 1: Use automated script
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your OpenAI API key
cd ..
./scripts/aws-deploy.sh

# Option 2: Manual Terraform commands
cd terraform
terraform init
terraform plan
terraform apply

# Destroy infrastructure
terraform destroy
```

### Manual Operations

```bash
# Install Python dependencies
pip install -r requirements.txt

# Create deployment package (manual)
rm -rf package deployment.zip
mkdir -p package
pip install -r requirements.txt -t package/
cp src/lambda_function.py package/
cp src/resume.md package/
cd package && zip -r ../deployment.zip . && cd ..

# Clean build artifacts
rm -rf package/ deployment.zip response.json output.json outputs.json

# Run code formatting (if you have black installed)
black src/

# Type checking (if you have mypy installed)
mypy src/lambda_function.py
```

## 🎯 Common Workflows

### First Time Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd virtualme

# 2. Set environment variable
export OPENAI_API_KEY="sk-proj-xxx"

# 3. Quick test
./scripts/quickstart.sh

# 4. Deploy to LocalStack
docker-compose up -d
./scripts/localstack-deploy.sh
```

### Update Knowledge Base and Redeploy

```bash
# 1. Edit your resume
nano src/resume.md  # or use any editor

# 2. Redeploy
# LocalStack:
./scripts/localstack-deploy.sh

# AWS:
cd terraform && terraform apply
```

### Debugging

```bash
# LocalStack logs
docker logs -f virtualme-localstack

# Test API endpoint
curl -X POST http://localhost:4566/restapis/API_ID/prod/_user_request_/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "text": "Hello"}]}'

# AWS CloudWatch logs
aws logs tail /aws/lambda/virtual-me-chatbot-prod --follow
```

## 📝 Script Details

### scripts/quickstart.sh
- Checks prerequisites (Python, OpenAI key)
- Installs dependencies
- Tests Lambda function locally
- Perfect for first-time setup validation

### scripts/localstack-deploy.sh
- Deploys complete stack to LocalStack
- Creates Lambda function
- Sets up API Gateway
- Tests deployment
- Returns API endpoint for frontend configuration

### scripts/aws-deploy.sh
- Runs full Terraform deployment to AWS
- Validates prerequisites
- Creates infrastructure
- Displays deployment summary with URLs

## 💡 Tips

1. **Always set OPENAI_API_KEY** before running scripts:
   ```bash
   export OPENAI_API_KEY="sk-proj-xxx"
   ```

2. **Use quickstart.sh first** to validate your setup

3. **For AWS deployments**, you can skip the script and use Terraform directly:
   ```bash
   cd terraform
   terraform init
   terraform apply
   ```

4. **Clean up regularly** to save space:
   ```bash
   rm -rf package/ deployment.zip
   ```

5. **Make scripts executable** if needed:
   ```bash
   chmod +x scripts/*.sh
   ```

## 🔄 Updating from Previous Version

If you had the Makefile version:

| Old Command | New Command |
|-------------|-------------|
| `make install` | `pip install -r requirements.txt` |
| `make localstack-up` | `docker-compose up -d` |
| `make localstack-deploy` | `./scripts/localstack-deploy.sh` |
| `make localstack-down` | `docker-compose down` |
| `make aws-deploy` | `./scripts/aws-deploy.sh` |
| `make test-local` | `cd src && python lambda_function.py` |
| `make clean` | `rm -rf package/ deployment.zip` |

## ❓ Need Help?

- See [README.md](README.md) for complete documentation
- See [QUICKSTART.md](QUICKSTART.md) for step-by-step guide
- See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
