# Virtual Me - AI-Powered Personal Chatbot with RAG

![Python](https://img.shields.io/badge/Python-3.11-blue)
![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange)
![LangChain](https://img.shields.io/badge/LangChain-Latest-green)
![Terraform](https://img.shields.io/badge/Terraform-IaC-purple)
![LocalStack](https://img.shields.io/badge/LocalStack-Local%20Dev-yellow)

A production-ready "Virtual Clone" chatbot that uses **Retrieval Augmented Generation (RAG)** to answer questions accurately based on your personal data (resume, bio, etc.). Built with AWS Lambda, LangChain, LangGraph, and FAISS for efficient vector similarity search.

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
                        │     ↓ (GPT-4o-mini)                 │
                        │  3. Response                        │
                        └─────────────────────────────────────┘
```

### RAG Data Flow

1. **Indexing** (Cold Start): `resume.md` → MarkdownHeaderTextSplitter → OpenAI Embeddings → FAISS Index
2. **Retrieval** (Per Request): User Question → Embedding → FAISS Search → Top 3 Relevant Chunks
3. **Generation**: System Prompt + Context + Question → GPT-4o-mini → Grounded Response

## 📁 Project Structure

```
virtualme/
├── src/                   # Lambda source code
│   ├── lambda_function.py # Backend (LangGraph + RAG)
│   └── resume.md         # Knowledge base (customize this!)
├── frontend/              # Frontend application
│   └── index.html        # Deep Chat UI
├── scripts/               # Deployment scripts
│   ├── localstack-deploy.sh  # LocalStack deployment
│   ├── aws-deploy.sh         # AWS production deployment
│   └── quickstart.sh         # Quick test script
├── terraform/             # AWS infrastructure (IaC)
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars.example
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # LocalStack configuration
├── .env.example          # Environment variables template
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose** (for LocalStack)
- **AWS CLI** (for production deployment)
- **Terraform** (for production deployment)
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))

### Option 1: Local Development with LocalStack

1. **Clone and Setup**
   ```bash
   git clone <your-repo>
   cd virtualme
   export OPENAI_API_KEY="sk-proj-xxxxxxxxxxxx"
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Quick Test (Optional)**
   ```bash
   ./scripts/quickstart.sh
   # This tests the Lambda function locally
   ```

4. **Start LocalStack and Deploy**
   ```bash
   docker-compose up -d
   ./scripts/localstack-deploy.sh
   ```

5. **Update Frontend**
   - Open `frontend/index.html`
   - Replace `API_ENDPOINT_PLACEHOLDER` with the endpoint shown in deployment output
   - Example: `http://localhost:4566/restapis/xxxxx/prod/_user_request_/chat`

6. **Test the Chatbot**
   - Open `frontend/index.html` in your browser
   - Start asking questions!

### Option 2: AWS Production Deployment

1. **Configure AWS Credentials**
   ```bash
   aws configure
   ```

2. **Setup Terraform Variables**
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars and add your OpenAI API key
   ```

3. **Deploy to AWS**
   ```bash
   cd terraform
   terraform init
   terraform plan
   terraform apply
   # or use the automated script: ../scripts/aws-deploy.sh
   ```

4. **Access Your Chatbot**
   - The deployment script will output the S3 website URL
   - No additional configuration needed - API endpoint is auto-injected!

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
   # LocalStack
   ./scripts/localstack-deploy.sh

   # AWS
   cd terraform && terraform apply
   ```

### Adjust RAG Parameters

In `src/lambda_function.py`:

```python
# Number of document chunks to retrieve
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}  # Increase for more context
)

# LLM temperature (lower = more factual)
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3  # 0.0-1.0
)
```

### Customize the UI

Edit `frontend/index.html` to change:
- Colors and styling (CSS variables)
- Initial messages
- Example questions
- Chat bubble styles

## 📊 Cost Analysis

### LocalStack (Free Tier)
- **Cost**: $0
- **Limitations**: Local only, not accessible from internet

### AWS Production (Estimated Monthly)
- **Lambda**: ~$0.20 per 1M requests + compute time
- **API Gateway**: ~$1.00 per 1M requests
- **S3**: ~$0.023 per GB stored (~$0.01/month for this project)
- **OpenAI API**: ~$0.15 per 1M tokens (GPT-4o-mini)

**Example**: 10,000 requests/month = ~$1.50/month (AWS) + ~$0.50/month (OpenAI) = **$2/month**

## 🧪 Testing

### Quick Test Script
```bash
export OPENAI_API_KEY="sk-proj-xxxx"
./scripts/quickstart.sh
```

### Test Lambda Locally
```bash
export OPENAI_API_KEY="sk-proj-xxxx"
cd src
python lambda_function.py
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

### Issue: OpenAI Rate Limits
**Solution**:
- Upgrade your OpenAI account tier
- Implement request caching
- Add rate limiting to API Gateway

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
4. **OpenAI API Latency**: Baseline ~500-1000ms

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
- **LocalStack** for enabling local AWS development
- **Deep Chat** for the beautiful chat UI component
- **OpenAI** for GPT-4o-mini and embeddings

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/virtualme/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/virtualme/discussions)
- **Email**: your.email@example.com

---

Built with ❤️ using AWS Lambda, LangChain, LangGraph, and FAISS

⭐ Star this repo if you find it useful!
