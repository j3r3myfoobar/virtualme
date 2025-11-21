# Virtual Me - AI-Powered Personal Chatbot with RAG

![Python](https://img.shields.io/badge/Python-3.11-blue)
![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange)
![LangChain](https://img.shields.io/badge/LangChain-Latest-green)
![Terraform](https://img.shields.io/badge/Terraform-IaC-purple)
![LocalStack](https://img.shields.io/badge/LocalStack-Local%20Dev-yellow)

A production-ready "Virtual Clone" chatbot that uses **Retrieval Augmented Generation (RAG)** to answer questions accurately based on your personal data (resume, bio, etc.). Built with AWS Lambda, AWS Bedrock (Llama 3.2), LangChain, LangGraph, and FAISS for efficient vector similarity search. Supports local development with LM Studio.

## 🌟 Features

- **RAG Architecture**: Grounds all responses in your provided knowledge base (no hallucinations!)
- **Serverless**: Cost-effective AWS Lambda + API Gateway architecture
- **Cold Start Optimized**: Strategic code organization minimizes Lambda initialization time
- **Beautiful UI**: Modern, responsive chat interface using Deep Chat web component
- **Local Development**: Full LocalStack support for development without AWS costs
- **Infrastructure as Code**: Complete Terraform configuration for reproducible deployments
- **Production Ready**: Includes logging, monitoring, and error handling

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
                        │     ↓ (FAISS Vector Search)         │
                        │  2. Generate Node                   │
                        │     ↓ (Bedrock: Llama 3.2)         │
                        │  3. Response                        │
                        └─────────────────────────────────────┘
```

### RAG Data Flow

1. **Indexing** (Cold Start): `resume.md` → MarkdownHeaderTextSplitter → Bedrock Titan Embeddings → FAISS Index
2. **Retrieval** (Per Request): User Question → Embedding → FAISS Search → Top 3 Relevant Chunks
3. **Generation**: System Prompt + Context + Question → Bedrock Llama 3.2 → Grounded Response

## 📁 Project Structure

```
virtualme/
├── src/                   # Lambda source code (modular)
│   ├── lambda_function.py # Entry point (Lambda handler)
│   ├── resume.md         # Knowledge base
│   ├── rag/              # RAG pipeline modules
│   │   ├── pipeline.py   # LangGraph orchestration
│   │   ├── retriever.py  # FAISS vector search
│   │   ├── generator.py  # LLM response generation
│   │   └── state.py      # State definitions
│   ├── loaders/          # Document loaders
│   │   └── knowledge_base.py
│   └── utils/            # Utility functions
│       └── http.py
├── frontend/              # Frontend application
│   └── index.html        # Deep Chat UI
├── scripts/               # Deployment scripts
│   ├── localstack-deploy.sh
│   ├── aws-deploy.sh
│   └── quickstart.sh
├── terraform/             # AWS infrastructure (IaC)
├── tests/                 # Unit and integration tests
│   ├── unit/
│   └── integration/
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # LocalStack configuration
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

4. **Deploy to AWS**
   ```bash
   cd terraform
   terraform init
   terraform plan
   terraform apply
   # or use the automated script: ../scripts/aws-deploy.sh
   ```

5. **Access Your Chatbot**
   - The deployment script will output the S3 website URL
   - No additional configuration needed - API endpoint is auto-injected!

### Model Switching

To switch between Bedrock models, update your environment variables:

```bash
# Use Claude instead of Llama
LLM_MODEL=claude-3-haiku

# Use different embedding model
EMBEDDING_MODEL=cohere-embed-english
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
- **S3**: ~$0.023 per GB stored (~$0.01/month for this project)
- **Bedrock Llama 3.2 3B**: ~$0.10 per 1M input tokens, ~$0.13 per 1M output tokens
- **Bedrock Titan Embeddings**: ~$0.10 per 1M tokens

**Example**: 10,000 requests/month = ~$1.50/month (AWS) + ~$0.50/month (Bedrock) = **$2/month**

**Cost Comparison**:
- **Llama 3.2 3B**: Most cost-effective, good quality
- **Llama 3.2 8B**: 2x cost, better reasoning
- **Claude 3 Haiku**: 3x cost, best quality

## 🧪 Testing

### Run Unit Tests
```bash
# All tests
python tests/test_all.py

# Individual test suites
python tests/unit/test_http.py
python tests/unit/test_knowledge_base.py
python tests/unit/test_lambda_handler.py
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
workflow.add_node("retrieve", retrieve_node)  # FAISS search
workflow.add_node("generate", generate_node)  # LLM call
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)
```

This creates a state machine that ensures proper data flow and error handling.

### Vector Store Selection

**Why FAISS?**
- ✅ In-memory (no external database needed)
- ✅ Fast similarity search (<10ms for small datasets)
- ✅ No additional AWS costs
- ✅ Perfect for <1000 documents

**Alternatives for larger datasets**:
- Pinecone (managed vector DB)
- Weaviate (self-hosted)
- Amazon OpenSearch

## 🔐 Security Best Practices

1. **Never commit API keys**: Use environment variables or AWS Secrets Manager
2. **Enable API Gateway throttling**: Prevent abuse
3. **Use AWS WAF**: Add web application firewall for production
4. **Restrict CORS**: Change `allow_origins` from `["*"]` to specific domains
5. **Enable CloudWatch Alarms**: Monitor errors and throttles

## 📈 Monitoring and Observability

### Key Metrics to Monitor

1. **Lambda Duration**: Should be <3s
2. **Lambda Errors**: Should be <1%
3. **API Gateway 4xx/5xx**: Track client and server errors
4. **Bedrock API Latency**: Baseline ~300-800ms (Llama 3.2), ~500-1000ms (Claude)

### CloudWatch Dashboard

Create a dashboard with:
```bash
aws cloudwatch put-dashboard \
  --dashboard-name VirtualMeChatbot \
  --dashboard-body file://dashboard.json
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
- **Meta** for the open Llama 3.2 models
- **LM Studio** for enabling local LLM development
- **LocalStack** for local AWS development
- **Deep Chat** for the beautiful chat UI component

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/virtualme/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/virtualme/discussions)
- **Email**: your.email@example.com

---

Built with ❤️ using AWS Lambda, AWS Bedrock, LangChain, LangGraph, and FAISS

⭐ Star this repo if you find it useful!
