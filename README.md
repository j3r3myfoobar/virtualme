# Virtual Me - AI-Powered Personal Chatbot with RAG

![Python](https://img.shields.io/badge/Python-3.11-blue)
![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange)
![LangChain](https://img.shields.io/badge/LangChain-Latest-green)
![Terraform](https://img.shields.io/badge/Terraform-IaC-purple)
![LocalStack](https://img.shields.io/badge/LocalStack-Local%20Dev-yellow)

A production-ready "Virtual Clone" chatbot that uses **Retrieval Augmented Generation (RAG)** to answer questions accurately based on your personal data (resume, bio, etc.). Built with AWS Lambda, AWS Bedrock (Nova 2 Lite), LangChain, LangGraph, and DynamoDB for persistent vector storage. Supports local development with LM Studio.

## 🌟 Features

- **RAG Architecture**: Grounds all responses in your provided knowledge base (no hallucinations!)
- **Serverless**: Cost-effective AWS Lambda + API Gateway architecture
- **Cold Start Optimized**: Strategic code organization minimizes Lambda initialization time
- **Beautiful UI**: Modern, responsive chat interface using Deep Chat web component
- **Local Development**: Full LocalStack support for development without AWS costs
- **Infrastructure as Code**: Complete Terraform configuration for reproducible deployments
- **Production Ready**: Pydantic validation, structured logging, retry logic, and timeout handling
- **Well Tested**: 37 unit tests covering core functionality

## 🏗️ Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Browser   │────────▶│ API Gateway  │────────▶│   Lambda    │
│  Deep Chat  │         │ (HTTP API)   │         │ (Python)    │
└─────────────┘         └──────────────┘         └──────┬──────┘
                                                          │
                                                          ▼
                        ┌─────────────────────────────────────┐
                        │      LangGraph RAG Pipeline         │
                        ├─────────────────────────────────────┤
                        │  1. Retrieve Node                   │
                        │     ↓ (DynamoDB Vector Search)      │
                        │  2. Generate Node                   │
                        │     ↓ (Bedrock: Nova 2 Lite)        │
                        │  3. Response                        │
                        └─────────────────────────────────────┘
```

### RAG Data Flow

1. **Indexing** (Cold Start): `resume.md` → MarkdownHeaderTextSplitter → Bedrock Titan Embeddings → DynamoDB Vector Store
2. **Retrieval** (Per Request): User Question → Embedding → DynamoDB Vector Search → Top 3 Relevant Chunks
3. **Generation**: System Prompt + Context + Question → Bedrock Nova 2 Lite → Grounded Response

## ☁️ AWS Services Used

### Core Services (Essential)

| Service | Purpose | Configuration | Cost Impact |
|---------|---------|---------------|-------------|
| **Lambda** | Main compute - runs the chatbot handler | Python 3.11, 512 MB, 30s timeout | 💰 Low (~$0.20/month) |
| **API Gateway** (HTTP API) | REST API endpoint for chatbot | HTTP API (cheaper than REST API) | 💰 Very Low (~$0.10/month) |
| **DynamoDB** | Vector storage for document embeddings | On-demand capacity | 💰💰 Medium (~$1-5/month) |
| **Bedrock** | LLM models (Nova 2 Lite) | Nova 2 Lite, temperature 0.1 | 💰 Low (~$0.50-2/month) |

### Frontend & CDN

| Service | Purpose | Configuration | Cost Impact |
|---------|---------|---------------|-------------|
| **S3** | Frontend hosting + Lambda deployment packages | 2 buckets (frontend, deployments) | 💰 Very Low (~$0.05/month) |
| **CloudFront** | CDN for frontend (https://chat.lemaire.tel) | Origin Access Identity (OAI) | 💰 Low (~$0.10/month) |

### Networking & DNS

| Service | Purpose | Configuration | Cost Impact |
|---------|---------|---------------|-------------|
| **Route53** | DNS for custom domains | lemaire.tel zone | 💰 Low ($0.50/month per hosted zone) |
| **ACM** (Certificate Manager) | SSL/TLS certificates | Wildcard cert for *.lemaire.tel | 💰 **Free** |

### Security & Access

| Service | Purpose | Configuration | Cost Impact |
|---------|---------|---------------|-------------|
| **IAM** | Roles and permissions | Lambda execution role + policies | 💰 **Free** |

### Monitoring & Operations

| Service | Purpose | Configuration | Cost Impact |
|---------|---------|---------------|-------------|
| **CloudWatch Logs** | Lambda and API Gateway logs | 7-day retention | 💰 Very Low (~$0.10/month) |
| **CloudWatch Alarms** | Error rate monitoring | SNS notifications | 💰 Very Low (~$0.10/month) |
| **X-Ray** | Distributed tracing | Active tracing enabled | 💰 Very Low (~$0.05/month) |
| **SNS** | Alert notifications | Alarm topic | 💰 Very Low (~$0.05/month) |

### Cost Summary

**Total Services: 13**

| Category | Estimated Monthly Cost |
|----------|----------------------|
| Lambda + API Gateway | $0.30 - $1.00 |
| DynamoDB | $1.00 - $5.00 |
| Bedrock (Nova 2 Lite) | $0.50 - $2.00 |
| S3 + CloudFront | $0.15 - $0.50 |
| Route53 | $0.50 |
| Monitoring | $0.25 - $0.50 |
| ACM & IAM | $0.00 (Free) |
| **Total** | **$2.70 - $9.50/month** |

*For personal use (~100 conversations/month), typically **$3-5/month***

## 📁 Project Structure

```
virtualme/
├── src/                   # Lambda source code (modular)
│   ├── lambda_function.py # Entry point (Lambda handler)
│   ├── config.py         # Pydantic settings and model configuration
│   ├── constants.py      # Application constants
│   ├── resume.md         # Knowledge base
│   ├── rag/              # RAG pipeline modules
│   │   ├── pipeline.py   # LangGraph orchestration
│   │   ├── dynamodb_retriever.py  # DynamoDB vector search
│   │   ├── generator.py  # LLM response generation
│   │   └── state.py      # State definitions
│   ├── loaders/          # Document loaders
│   │   └── knowledge_base.py
│   ├── models/           # Pydantic request/response models
│   │   └── requests.py
│   ├── vectorstores/     # Vector store implementations
│   │   └── dynamodb_vector_store.py
│   └── utils/            # Utility functions
│       ├── http.py       # HTTP response helpers
│       └── logging.py    # Centralized logging configuration
├── frontend/              # Frontend application
│   └── index.html        # Deep Chat UI
├── terraform/             # AWS infrastructure (IaC)
├── tests/                 # Unit tests (37 tests)
│   ├── unit/
│   │   ├── test_generator.py
│   │   ├── test_vector_store.py
│   │   ├── test_http.py
│   │   └── ...
│   └── conftest.py       # Shared pytest fixtures
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

**Note:** Code is organized into modules locally but deploys as a **single Lambda function**. See [src/README.md](src/README.md) for module details.

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **AWS Account** with Bedrock access ([Request access here](https://console.aws.amazon.com/bedrock))
- **AWS CLI** configured with credentials
- **Terraform** (for production deployment)
- **Docker & Docker Compose** (optional, for LocalStack)
- **LM Studio** (optional, for local development - [Download here](https://lmstudio.ai))

### Option 1: Local Development with LM Studio

1. **Clone and Setup**
   ```bash
   git clone <your-repo>
   cd virtualme
   cp .env.example .env
   ```

2. **Configure LM Studio**
   - Download and install [LM Studio](https://lmstudio.ai)
   - Download a model (e.g., Llama 3.2 3B Instruct)
   - Start the local server (default: http://localhost:1234/v1)

3. **Configure Environment**
   Edit `.env`:
   ```bash
   LLM_BACKEND=lm_studio
   LLM_MODEL=llama-3.2-3b-instruct
   LLM_TEMPERATURE=0.3
   EMBEDDING_BACKEND=bedrock  # Or use openai for local testing
   EMBEDDING_MODEL=titan-embed-text-v2
   AWS_REGION=us-east-1
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Quick Test**
   ```bash
   ./scripts/quickstart.sh
   # This tests the Lambda function locally with LM Studio
   ```

### Option 2: AWS Production Deployment with Bedrock

1. **Enable Bedrock Models**
   - Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock)
   - Request access to Llama 3.2 models and Titan Embeddings
   - Wait for approval (usually instant for Titan, may take time for Llama)

2. **Configure AWS Credentials**
   ```bash
   aws configure
   # Enter your AWS Access Key ID and Secret Access Key
   ```

3. **Setup Terraform Variables**
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars to configure models
   ```

   Example configuration:
   ```hcl
   llm_model       = "llama-3.2-3b"      # Or claude-3-haiku
   embedding_model = "titan-embed-text-v2"
   llm_temperature = "0.3"
   ```

4. **(Optional) Setup Remote State Backend**
   ```bash
   # For team collaboration and state locking
   ./scripts/setup-terraform-backend.sh
   cd terraform
   cp backend.tf.example backend.tf
   # Update YOUR-ACCOUNT-ID in backend.tf
   ```

5. **Deploy to AWS**
   ```bash
   cd terraform
   terraform init
   terraform plan  # Review changes
   terraform apply # Deploy infrastructure
   # or use the automated script: ../scripts/aws-deploy.sh
   ```

6. **Configure CloudWatch Alarms (Optional)**
   ```bash
   # Subscribe to SNS topic for email alerts
   aws sns subscribe \
     --topic-arn $(terraform output -raw sns_topic_arn) \
     --protocol email \
     --notification-endpoint your-email@example.com
   ```

7. **Access Your Chatbot**
   - Frontend: https://chat.lemaire.tel
   - API: https://api.lemaire.tel/chat
   - CloudWatch Alarms: AWS Console → CloudWatch
   - X-Ray Traces: AWS Console → X-Ray

### Model Switching

To switch between Bedrock models, update your environment variables:

```bash
# Available models (see src/config.py for full list)
LLM_MODEL=nova-2-lite      # Default - best price/performance (re:Invent 2025)
LLM_MODEL=nova-2-pro       # More capable, higher cost
LLM_MODEL=claude-3-haiku   # Anthropic alternative

# Use different embedding model
EMBEDDING_MODEL=titan-embed-text-v2  # Default
```

For Terraform deployments, update `terraform/terraform.tfvars` and run `terraform apply`.

## 🛠️ Customization

### Update Your Knowledge Base

1. **Edit `src/resume.md`** with your own information:
   ```markdown
   # Your Name

   ## Professional Summary
   Your background and expertise...

   ## Experience
   ### Company Name
   Your role and achievements...
   ```

2. **Redeploy**:
   ```bash
   # Local test
   cd src && python lambda_function.py

   # AWS
   cd terraform && terraform apply
   ```

### Adjust RAG Parameters

Edit `.env` (local) or `terraform/terraform.tfvars` (AWS):

```bash
# Number of document chunks to retrieve (in src/rag/retriever.py)
search_kwargs={"k": 3}  # Increase for more context

# LLM temperature (lower = more factual, higher = creative)
LLM_TEMPERATURE=0.3  # Range: 0.0-1.0

# Switch models easily
LLM_MODEL=llama-3.2-3b        # Fast, cost-effective
# LLM_MODEL=llama-3.2-8b      # More capable
# LLM_MODEL=claude-3-haiku    # Best quality
```

### Customize the UI

Edit `frontend/index.html` to change:
- Colors and styling (CSS variables)
- Initial messages
- Example questions
- Chat bubble styles

## 📊 Cost Analysis

### Local Development (Free)
- **LM Studio**: $0 (run models on your machine)
- **Limitations**: Requires GPU for good performance

### AWS Production with Bedrock (Estimated Monthly)
- **Lambda**: ~$0.20 per 1M requests + compute time
- **API Gateway**: ~$1.00 per 1M requests
- **S3**: ~$0.023 per GB stored (~$0.01/month for frontend + state)
- **DynamoDB**: Pay-per-request (~$1.25 per 1M reads, ~$6.25 per 1M writes)
- **CloudWatch**: First 10 alarms free, $0.10/alarm/month after
- **X-Ray**: First 100,000 traces/month free, $5 per 1M traces after
- **Bedrock Llama 3.2 3B**: ~$0.10 per 1M input tokens, ~$0.13 per 1M output tokens
- **Bedrock Titan Embeddings**: ~$0.10 per 1M tokens

**Example (10,000 requests/month)**:
- AWS Services: ~$1.50/month (Lambda + API Gateway + S3)
- DynamoDB: ~$0.15/month (10k reads for retrieval)
- Bedrock: ~$0.50/month (LLM + embeddings)
- **Total: ~$2.15/month**

**Cost Comparison** (per 1M tokens):
| Model | Input | Output | Notes |
|-------|-------|--------|-------|
| **Nova 2 Lite** | $0.06 | $0.24 | Default - best value |
| **Nova 2 Pro** | $0.80 | $3.20 | Extended thinking |
| **Claude 3 Haiku** | $0.25 | $1.25 | Anthropic alternative |

**Cost Optimization Tips**:
- DynamoDB on-demand pricing perfect for low traffic
- X-Ray sampling reduces trace costs
- CloudWatch log retention set to 7 days (configurable)

## 🧪 Testing

### Run Unit Tests
```bash
# All tests (37 tests)
python -m pytest tests/ -v

# Individual test suites
python -m pytest tests/unit/test_vector_store.py -v
python -m pytest tests/unit/test_generator.py -v
python -m pytest tests/unit/test_http.py -v
```

### Quick Test Script
```bash
# Ensure .env is configured with LM_STUDIO or BEDROCK backend
./scripts/quickstart.sh
```

### Test Lambda Locally
```bash
# With .env file configured
cd src
python lambda_function.py

# Or with environment variables
LLM_BACKEND=lm_studio LLM_MODEL=llama-3.2-3b-instruct python lambda_function.py
```

### Test with Sample Request
```bash
curl -X POST http://localhost:4566/restapis/xxxxx/prod/_user_request_/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "text": "What is your main expertise?"}
    ]
  }'
```

### View Logs

**LocalStack**:
```bash
docker logs -f virtualme-localstack
```

**AWS**:
```bash
aws logs tail /aws/lambda/virtual-me-chatbot-prod --follow
```

## 🐛 Troubleshooting

### Issue: Lambda Timeout
**Solution**: Increase timeout in `terraform/main.tf`:
```hcl
resource "aws_lambda_function" "virtual_me" {
  timeout = 60  # Increase from 30
}
```

### Issue: CORS Errors
**Solution**: Verify API Gateway CORS settings in `terraform/main.tf`:
```hcl
cors_configuration {
  allow_origins = ["*"]
  allow_methods = ["POST", "OPTIONS"]
  allow_headers = ["content-type"]
}
```

### Issue: Bedrock Throttling
**Solution**:
- Request quota increase in AWS Service Quotas console
- Implement exponential backoff retry logic
- Add rate limiting to API Gateway
- Consider switching to a larger model tier

### Issue: Large Deployment Package
**Solution**: Use Lambda Layers for dependencies:
```bash
# Create layer
pip install -r requirements.txt -t python/
zip -r layer.zip python/

# Upload to AWS Lambda Layers
aws lambda publish-layer-version \
  --layer-name virtualme-dependencies \
  --zip-file fileb://layer.zip
```

## 📚 Technical Deep Dive

### Cold Start Optimization

The `lambda_function.py` loads the vector store **outside** the handler:

```python
# Global scope - runs once per container
retriever = load_knowledge_base()

def lambda_handler(event, context):
    # This runs per request
    result = app.invoke(initial_state)
```

**Impact**:
- First invocation: ~3-5 seconds (cold start)
- Subsequent invocations: ~200-500ms (warm)

### LangGraph Workflow

```python
workflow = StateGraph(GraphState)
workflow.add_node("retrieve", retrieve_node)  # DynamoDB vector search
workflow.add_node("generate", generate_node)  # LLM call
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)
```

This creates a state machine that ensures proper data flow and error handling.

### Vector Store Selection

**Why DynamoDB?**
- ✅ Persistent storage (survives Lambda cold starts)
- ✅ Serverless and scalable (no infrastructure to manage)
- ✅ Fast similarity search with custom vector implementation
- ✅ Integrated with AWS ecosystem
- ✅ Pay-per-request pricing (cost-effective for low traffic)

**Benefits over in-memory solutions**:
- No need to rebuild index on every cold start
- State persists across deployments
- Can handle larger datasets without memory constraints

## 🔐 Security Best Practices

This project implements production-grade security measures:

1. **IAM Least Privilege**: Lambda IAM policies scoped to specific resources only
2. **CORS Restricted**: API Gateway only accepts requests from `https://chat.lemaire.tel`
3. **No Sensitive Data in Logs**: Error details logged internally, generic messages returned to clients
4. **API Rate Limiting**: 50 requests/second, 100 burst limit to prevent abuse
5. **Encrypted State**: S3 backend encryption enabled, DynamoDB encryption at rest
6. **X-Ray Tracing**: Full request tracing without exposing sensitive data
7. **CloudWatch Alarms**: Automated monitoring for security events

**Additional Recommendations**:
- Use AWS Secrets Manager for sensitive configuration
- Enable AWS WAF for additional protection
- Regularly rotate AWS credentials
- Review CloudWatch logs for suspicious activity

## 📈 Monitoring and Observability

This project includes comprehensive production monitoring:

### CloudWatch Alarms (Auto-configured)

**Lambda Alarms:**
- Errors: >5 errors in 2 minutes
- Throttles: Any throttling detected
- Duration: Average >25 seconds (near timeout)
- Concurrent Executions: >50 concurrent invocations

**API Gateway Alarms:**
- 5xx Errors: >5 server errors in 1 minute
- 4xx Errors: >50 client errors in 5 minutes

**SNS Topic**: `virtual-me-chatbot-prod-alarms`
- Configure email/SMS subscriptions in AWS Console

### X-Ray Tracing

Full distributed tracing enabled:
- API Gateway → Lambda → Bedrock → DynamoDB
- View traces: AWS Console → X-Ray → Service Map
- Identify bottlenecks and latency issues
- Debug production issues without additional logging

### Key Metrics to Monitor

1. **Lambda Duration**: Should be <3s (cold start may be higher)
2. **Lambda Errors**: Target <1%
3. **API Gateway 4xx/5xx**: Track client and server errors
4. **Bedrock API Latency**: Baseline ~300-800ms (Llama 3.2)
5. **DynamoDB Read/Write**: Monitor consumed capacity

### Accessing Monitoring

**CloudWatch Alarms:**
```bash
aws cloudwatch describe-alarms --alarm-names \
  virtual-me-chatbot-prod-errors \
  virtual-me-chatbot-prod-throttles
```

**X-Ray Traces:**
```bash
# View service map
aws xray get-service-graph --start-time $(date -u -d '1 hour ago' +%s) --end-time $(date +%s)
```

**Lambda Logs:**
```bash
aws logs tail /aws/lambda/virtual-me-chatbot-prod --follow
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally with LocalStack
5. Submit a pull request

## 📄 License

MIT License - feel free to use this for personal or commercial projects!

## 🙏 Acknowledgments

- **LangChain** for the excellent RAG framework
- **AWS Bedrock** for serverless LLM infrastructure
- **Amazon Nova 2** for cost-effective, capable AI models
- **LM Studio** for enabling local LLM development
- **Deep Chat** for the beautiful chat UI component
- **Pydantic** for robust data validation

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/virtualme/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/virtualme/discussions)
- **Email**: your.email@example.com

---

Built with ❤️ using AWS Lambda, AWS Bedrock (Nova 2 Lite), LangChain, LangGraph, and DynamoDB

⭐ Star this repo if you find it useful!
