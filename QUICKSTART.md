# Virtual Me - Quick Start Guide

Get your Virtual Me chatbot running in under 5 minutes!

## Prerequisites Checklist

- [ ] Python 3.11+ installed (`python --version`)
- [ ] AWS CLI configured (`aws configure`)
- [ ] AWS Bedrock access enabled (for production)
- [ ] LM Studio installed (optional, for local dev - [Download here](https://lmstudio.ai))
- [ ] Docker installed (optional, for LocalStack - `docker --version`)

## Option 1: Local Development with LM Studio (Fastest)

### Step 1: Clone and Setup
```bash
git clone <your-repo>
cd virtualme
cp .env.example .env
```

### Step 2: Setup LM Studio
1. Download and install [LM Studio](https://lmstudio.ai)
2. Download a model (e.g., "Llama 3.2 3B Instruct")
3. Start the local server:
   - Click "Local Server" tab in LM Studio
   - Load your model
   - Start server (default: http://localhost:1234/v1)

### Step 3: Configure Environment
Edit `.env` file:
```bash
LLM_BACKEND=lm_studio
LLM_MODEL=llama-3.2-3b-instruct
LLM_TEMPERATURE=0.3
EMBEDDING_BACKEND=bedrock  # Requires AWS credentials
EMBEDDING_MODEL=titan-embed-text-v2
AWS_REGION=us-east-1
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Quick Test
```bash
./scripts/quickstart.sh
```

You should see output like:
```json
{
  "statusCode": 200,
  "body": {
    "text": "I'm a Senior Software Engineer with 8+ years of experience..."
  }
}
```

### Step 6: Customize Your Knowledge Base
Edit `src/resume.md` with your own information:
```bash
nano src/resume.md  # or use any text editor
```

### Step 7: Test Again
```bash
cd src && python lambda_function.py
```

**Success!** Your Virtual Me is working locally with LM Studio.

---

## Option 2: LocalStack (Full AWS Simulation)

### Step 1: Start LocalStack
```bash
docker-compose up -d
# Wait ~10 seconds for LocalStack to initialize
```

### Step 2: Configure Environment
```bash
# Create .env file with your settings
cp .env.example .env
# Edit .env to use lm_studio backend
```

### Step 3: Deploy to LocalStack
```bash
./scripts/localstack-deploy.sh
```

### Step 4: Get Your API Endpoint
Look for this in the output:
```
API Endpoint: http://localhost:4566/restapis/xxxxx/prod/_user_request_/chat
```

### Step 5: Update Frontend
1. Open `frontend/index.html` in a text editor
2. Find this line:
   ```javascript
   const API_ENDPOINT = 'API_ENDPOINT_PLACEHOLDER';
   ```
3. Replace with your endpoint:
   ```javascript
   const API_ENDPOINT = 'http://localhost:4566/restapis/xxxxx/prod/_user_request_/chat';
   ```
4. Save the file

### Step 6: Open the Chatbot
```bash
# macOS
open frontend/index.html

# Linux
xdg-open frontend/index.html

# Windows
start frontend/index.html
```

**That's it!** Start chatting with your Virtual Me.

---

## Option 3: AWS Production Deployment with Bedrock

### Step 1: Enable Bedrock Access
1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock)
2. Request access to:
   - Meta Llama 3.2 models (1B, 3B, 8B)
   - Amazon Titan Embeddings
3. Wait for approval (usually instant)

### Step 2: Configure AWS
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter region (e.g., us-east-1)
```

### Step 3: Setup Terraform Variables
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
# Model configuration
llm_model       = "llama-3.2-3b"      # Or claude-3-haiku
embedding_model = "titan-embed-text-v2"
llm_temperature = "0.3"

# AWS configuration
aws_region  = "us-east-1"
environment = "prod"
```

### Step 3: Deploy
```bash
# Option 1: Use the automated script
cd ..
./scripts/aws-deploy.sh

# Option 2: Manual Terraform
cd terraform
terraform init
terraform plan
terraform apply
```

This will:
1. Create Lambda function
2. Create API Gateway
3. Create S3 bucket for frontend
4. Upload and configure everything

### Step 5: Get Your URL
After deployment completes, look for:
```
Chatbot URL: http://virtual-me-chatbot-frontend-prod-123456.s3-website-us-east-1.amazonaws.com
```

### Step 6: Open and Test
Copy the URL and open it in your browser. Done!

---

## Troubleshooting

### Issue: "ModuleNotFoundError"
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
# or use quickstart script:
./scripts/quickstart.sh
```

### Issue: "AWS credentials not configured"
**Solution**: Configure AWS CLI
```bash
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="us-east-1"
```

### Issue: LocalStack not responding
**Solution**: Check if Docker is running
```bash
docker ps
# Should show virtualme-localstack container
```

If not running:
```bash
docker-compose down
docker-compose up -d
```

### Issue: "Permission denied" on scripts
**Solution**: Make scripts executable
```bash
chmod +x scripts/*.sh
```

### Issue: Lambda timeout in AWS
**Solution**: Check CloudWatch logs
```bash
aws logs tail /aws/lambda/virtual-me-chatbot-prod --follow
```

Common causes:
- Bedrock throttling (request quota increase)
- Large resume causing slow embeddings
- Network issues
- Model not enabled in Bedrock console

**Fix**: Increase timeout in `terraform/main.tf`:
```hcl
timeout = 60  # Increase from 30
```

Then redeploy:
```bash
cd terraform && terraform apply
```

---

## What's Next?

### Customize Your Virtual Me

1. **Update resume.md** with your information
2. **Test locally** to verify responses
3. **Redeploy** using `./scripts/localstack-deploy.sh` or `./scripts/aws-deploy.sh`

### Add More Features

- Implement caching for faster responses
- Add authentication with AWS Cognito
- Set up custom domain with Route53
- Enable HTTPS with CloudFront + ACM

See [ARCHITECTURE.md](ARCHITECTURE.md) for advanced topics.

### Monitor Your Chatbot

**LocalStack**:
```bash
docker logs -f virtualme-localstack
```

**AWS**:
```bash
# Lambda logs
aws logs tail /aws/lambda/virtual-me-chatbot-prod --follow

# API Gateway logs
aws logs tail /aws/apigateway/virtual-me-api-prod --follow
```

---

## Cost Estimates

### Local Development (LM Studio)
**Cost**: $0 (completely free, runs on your machine)

### AWS with Bedrock (Monthly)
- **Lambda**: $0.20 per 1M requests
- **API Gateway**: $1.00 per 1M requests
- **S3**: $0.023 per GB (~$0.01 for this project)
- **CloudWatch**: ~$0.50 for logs
- **Bedrock Llama 3.2 3B**: ~$0.10 per 1M input tokens, ~$0.13 per 1M output tokens
- **Bedrock Titan Embeddings**: ~$0.10 per 1M tokens

**Example** (10,000 requests/month):
- Lambda: $0.002
- API Gateway: $0.01
- S3: $0.01
- CloudWatch: $0.50
- Bedrock: ~$0.50 (Llama 3.2 3B + Titan embeddings)
- **Total**: ~$1.00-$2.00/month

**AWS Free Tier** (first 12 months):
- 1M Lambda requests/month free
- 1M API Gateway requests/month free
- 5GB S3 storage free

**Model Cost Comparison**:
- **Llama 3.2 3B**: Most cost-effective
- **Llama 3.2 8B**: ~2x cost, better quality
- **Claude 3 Haiku**: ~3-5x cost, premium quality

---

## Need Help?

- **Documentation**: [README.md](README.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/virtualme/issues)

---

**Congratulations!** You now have a fully functional AI-powered Virtual Me chatbot. 🎉

Start customizing `resume.md` and make it truly yours!
