# Virtual Me - Quick Start Guide

Get your Virtual Me chatbot running in under 5 minutes!

## Prerequisites Checklist

- [ ] Python 3.11+ installed (`python --version`)
- [ ] Docker installed (`docker --version`)
- [ ] OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Option 1: Local Development (Fastest)

### Step 1: Clone and Setup
```bash
git clone <your-repo>
cd virtualme
```

### Step 2: Set Your OpenAI API Key
```bash
export OPENAI_API_KEY="sk-proj-xxxxxxxxxxxxxxxxxxxxx"
```

**Windows (PowerShell)**:
```powershell
$env:OPENAI_API_KEY="sk-proj-xxxxxxxxxxxxxxxxxxxxx"
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Test Locally (No Docker Required)
```bash
python lambda_function.py
```

You should see a response like:
```json
{
  "statusCode": 200,
  "body": {
    "text": "I'm a Senior Software Engineer with 8+ years of experience..."
  }
}
```

### Step 5: Customize Your Knowledge Base
Edit `resume.md` with your own information:
```bash
nano resume.md  # or use any text editor
```

### Step 6: Test Again
```bash
python lambda_function.py
```

**Success!** Your Virtual Me is working locally. Now let's deploy it.

---

## Option 2: LocalStack (Full AWS Simulation)

### Step 1: Start LocalStack
```bash
make localstack-up
# Wait ~10 seconds for LocalStack to initialize
```

### Step 2: Deploy to LocalStack
```bash
export OPENAI_API_KEY="sk-proj-xxxxxxxxxxxxxxxxxxxxx"
make localstack-deploy
```

### Step 3: Get Your API Endpoint
Look for this in the output:
```
API Endpoint: http://localhost:4566/restapis/xxxxx/prod/_user_request_/chat
```

### Step 4: Update Frontend
1. Open `index.html` in a text editor
2. Find this line:
   ```javascript
   const API_ENDPOINT = 'API_ENDPOINT_PLACEHOLDER';
   ```
3. Replace with your endpoint:
   ```javascript
   const API_ENDPOINT = 'http://localhost:4566/restapis/xxxxx/prod/_user_request_/chat';
   ```
4. Save the file

### Step 5: Open the Chatbot
```bash
# macOS
open index.html

# Linux
xdg-open index.html

# Windows
start index.html
```

**That's it!** Start chatting with your Virtual Me.

---

## Option 3: AWS Production Deployment

### Step 1: Configure AWS
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter region (e.g., us-east-1)
```

### Step 2: Setup Terraform Variables
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
openai_api_key = "sk-proj-xxxxxxxxxxxxxxxxxxxxx"  # Your key here
aws_region     = "us-east-1"
environment    = "prod"
```

### Step 3: Deploy
```bash
make aws-deploy
```

This will:
1. Create Lambda function
2. Create API Gateway
3. Create S3 bucket for frontend
4. Upload and configure everything

### Step 4: Get Your URL
After deployment completes, look for:
```
Chatbot URL: http://virtual-me-chatbot-frontend-prod-123456.s3-website-us-east-1.amazonaws.com
```

### Step 5: Open and Test
Copy the URL and open it in your browser. Done!

---

## Troubleshooting

### Issue: "ModuleNotFoundError"
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "OPENAI_API_KEY not set"
**Solution**: Export the key
```bash
export OPENAI_API_KEY="sk-proj-xxxxxxxxxxxxxxxxxxxxx"
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
chmod +x localstack-deploy.sh terraform/deploy.sh
```

### Issue: Lambda timeout in AWS
**Solution**: Check CloudWatch logs
```bash
aws logs tail /aws/lambda/virtual-me-chatbot-prod --follow
```

Common causes:
- OpenAI API rate limits
- Large resume causing slow embeddings
- Network issues

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
3. **Redeploy** using `make localstack-deploy` or `make aws-deploy`

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

### LocalStack
**Cost**: $0 (completely free)

### AWS (Monthly)
- **Lambda**: $0.20 per 1M requests
- **API Gateway**: $1.00 per 1M requests
- **S3**: $0.023 per GB (~$0.01 for this project)
- **CloudWatch**: ~$0.50 for logs
- **OpenAI**: ~$0.15 per 1M tokens (GPT-4o-mini)

**Example** (10,000 requests/month):
- Lambda: $0.002
- API Gateway: $0.01
- S3: $0.01
- CloudWatch: $0.50
- OpenAI: ~$1.00
- **Total**: ~$1.50/month

**AWS Free Tier** (first 12 months):
- 1M Lambda requests/month free
- 1M API Gateway requests/month free
- 5GB S3 storage free

---

## Need Help?

- **Documentation**: [README.md](README.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/virtualme/issues)

---

**Congratulations!** You now have a fully functional AI-powered Virtual Me chatbot. 🎉

Start customizing `resume.md` and make it truly yours!
