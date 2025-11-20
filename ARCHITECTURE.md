# Virtual Me - Technical Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [RAG Pipeline Deep Dive](#rag-pipeline-deep-dive)
3. [Component Architecture](#component-architecture)
4. [Performance Optimization](#performance-optimization)
5. [Security Architecture](#security-architecture)
6. [Scaling Considerations](#scaling-considerations)

## System Overview

The Virtual Me chatbot implements a **Retrieval Augmented Generation (RAG)** pattern to create an AI-powered personal assistant that answers questions strictly based on provided personal data.

### Key Design Principles

1. **Grounded Responses**: All answers must be derivable from the knowledge base
2. **Cost Efficiency**: Serverless architecture with pay-per-use pricing
3. **Low Latency**: Cold start optimization for sub-second warm responses
4. **Simplicity**: Minimal external dependencies, in-memory vector store
5. **Reproducibility**: IaC with Terraform ensures consistent deployments

## RAG Pipeline Deep Dive

### Phase 1: Knowledge Base Indexing (Cold Start)

```
┌──────────────┐
│  resume.md   │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────┐
│ MarkdownHeaderTextSplitter       │
│ - Headers: #, ##, ###            │
│ - Maintains hierarchical context │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│ Text Chunks with Metadata        │
│ Example:                         │
│ {                                │
│   content: "8+ years exp...",    │
│   metadata: {                    │
│     "Header 1": "John Doe",      │
│     "Header 2": "Experience"     │
│   }                              │
│ }                                │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│ OpenAI Embeddings                │
│ Model: text-embedding-ada-002    │
│ Dimensions: 1536                 │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│ FAISS Index (In-Memory)          │
│ - IndexFlatL2 (exact search)     │
│ - Stored in Lambda memory        │
└──────────────────────────────────┘
```

**Code Reference**: `lambda_function.py:load_knowledge_base()`

```python
# Split markdown maintaining header context
markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ],
    strip_headers=False
)

splits = markdown_splitter.split_text(resume_content)

# Create FAISS vector store
embeddings = OpenAIEmbeddings(openai_api_key=os.environ.get('OPENAI_API_KEY'))
vectorstore = FAISS.from_documents(splits, embeddings)
```

### Phase 2: Query Processing (Per Request)

```
User Question
    │
    ▼
┌──────────────────────────────────┐
│ OpenAI Embeddings                │
│ Convert text to 1536-dim vector  │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│ FAISS Similarity Search          │
│ - Compute L2 distance            │
│ - Return top k=3 chunks          │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│ Context Assembly                 │
│ Format chunks with metadata      │
└──────────────────────────────────┘
```

**Code Reference**: `lambda_function.py:retrieve_node()`

```python
def retrieve_node(state: GraphState) -> dict:
    question = state["question"]

    # Retrieve relevant documents
    documents = retriever.get_relevant_documents(question)

    # Format context from retrieved documents
    context = "\n\n".join([
        f"Section: {doc.metadata.get('Header 2', 'N/A')}\n{doc.page_content}"
        for doc in documents
    ])

    return {"context": context}
```

### Phase 3: Response Generation

```
┌──────────────────────────────────┐
│ System Prompt                    │
│ - Defines persona               │
│ - Sets constraints              │
│ - Emphasizes grounding          │
└──────────┬───────────────────────┘
           │
           ├─────────────┐
           │             │
           ▼             ▼
      Context      User Question
           │             │
           └──────┬──────┘
                  │
                  ▼
┌──────────────────────────────────┐
│ ChatOpenAI (GPT-4o-mini)         │
│ Temperature: 0.3                 │
│ Max tokens: Default (~1000)      │
└──────────┬───────────────────────┘
           │
           ▼
    Grounded Response
```

**System Prompt Architecture**:

```python
system_prompt = """You are a Virtual Clone chatbot representing the person described in the provided context.

CRITICAL RULES:
1. Answer ONLY based on the provided CONTEXT below
2. If the question cannot be answered from the CONTEXT, say: "I don't have that information in my profile."
3. Respond in first person as if you ARE the person in the resume
4. Be conversational, friendly, and professional
5. Never make up or hallucinate information not present in the CONTEXT
6. Keep responses concise (2-4 sentences unless more detail is explicitly requested)

CONTEXT:
{context}

Remember: You are speaking AS this person, not ABOUT them."""
```

### LangGraph State Machine

```
START
  │
  ▼
┌──────────────┐
│ retrieve_node│  (Fetches context from FAISS)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ generate_node│  (Calls GPT-4o-mini)
└──────┬───────┘
       │
       ▼
      END
```

**State Definition**:

```python
class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add]
    context: str
    question: str
```

## Component Architecture

### 1. Frontend (index.html)

**Technology**: Deep Chat Web Component

**Key Features**:
- Zero-dependency chat UI
- Built-in message history management
- Customizable styling
- Automatic request formatting

**Request Format**:
```json
{
  "messages": [
    {"role": "user", "text": "First question"},
    {"role": "ai", "text": "First answer"},
    {"role": "user", "text": "Second question"}
  ]
}
```

**Note**: Lambda processes only the **last user message** for stateless RAG.

### 2. API Gateway (HTTP API)

**Type**: AWS API Gateway HTTP API (not REST API)

**Why HTTP API?**
- 71% cheaper than REST API
- Lower latency (~50ms vs ~100ms)
- Built-in CORS support
- Simpler configuration

**Route Configuration**:
- `POST /chat` → Lambda integration
- `OPTIONS /chat` → CORS preflight (handled by Lambda)

**Pricing**: $1.00 per million requests

### 3. Lambda Function (lambda_function.py)

**Runtime**: Python 3.11
**Memory**: 512 MB (optimal for FAISS + embeddings)
**Timeout**: 30 seconds
**Cold Start**: ~3-5 seconds
**Warm Latency**: ~200-500ms

**Memory Breakdown**:
- Python runtime: ~50 MB
- LangChain + dependencies: ~150 MB
- FAISS index (small resume): ~10 MB
- Working memory: ~100 MB
- **Total**: ~310 MB (512 MB provides headroom)

### 4. Vector Store (FAISS)

**Why FAISS?**

| Feature | FAISS | Pinecone | Weaviate |
|---------|-------|----------|----------|
| Cost | Free | $0.10/1M queries | $25/month |
| Latency | <10ms | ~50-100ms | ~50ms |
| Setup | In-memory | Managed | Self-hosted |
| Scalability | <1000 docs | Millions | Millions |

**Index Type**: `IndexFlatL2` (exact L2 distance)

**Alternative for large datasets**: `IndexIVFFlat` with clustering

## Performance Optimization

### Cold Start Mitigation

**Problem**: Lambda containers are initialized on first request or after inactivity.

**Solution**: Load vector store at module level

```python
# ❌ BAD: Loads on every request
def lambda_handler(event, context):
    retriever = load_knowledge_base()  # 3-5 seconds
    # ...

# ✅ GOOD: Loads once per container
retriever = load_knowledge_base()  # Cold start only

def lambda_handler(event, context):
    # retriever already in memory
    # ...
```

**Impact**:
- First request: 3-5 seconds
- Subsequent requests (same container): 200-500ms
- Container reuse: ~15 minutes of inactivity

**Advanced Optimization**: Provisioned Concurrency
```hcl
resource "aws_lambda_provisioned_concurrency_config" "warm" {
  function_name = aws_lambda_function.virtual_me.function_name
  provisioned_concurrent_executions = 1
}
```
**Cost**: ~$13/month for 1 pre-warmed container

### Response Latency Breakdown

| Component | Time | Optimization |
|-----------|------|--------------|
| API Gateway | 10-20ms | N/A (managed service) |
| Lambda Init | 50-100ms | Minimize imports |
| FAISS Search | 5-15ms | Use IndexIVFFlat for large datasets |
| OpenAI Embedding | 100-200ms | Batch requests if possible |
| GPT-4o-mini | 500-1000ms | Use streaming for better UX |
| **Total** | **665-1335ms** | |

### Caching Strategy

**Option 1**: API Gateway Cache (not supported for HTTP API)

**Option 2**: DynamoDB Cache

```python
import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
cache_table = dynamodb.Table('virtual-me-cache')

def get_cached_response(question_hash):
    response = cache_table.get_item(Key={'question_hash': question_hash})
    if 'Item' in response:
        expiry = datetime.fromisoformat(response['Item']['expiry'])
        if datetime.now() < expiry:
            return response['Item']['answer']
    return None

def cache_response(question_hash, answer, ttl_hours=24):
    expiry = datetime.now() + timedelta(hours=ttl_hours)
    cache_table.put_item(Item={
        'question_hash': question_hash,
        'answer': answer,
        'expiry': expiry.isoformat()
    })
```

**Option 3**: Lambda@Edge + CloudFront (for global distribution)

## Security Architecture

### 1. API Security

**Current**: Public API (no authentication)

**Production Recommendations**:

```hcl
# Lambda authorizer for custom auth
resource "aws_apigatewayv2_authorizer" "lambda_auth" {
  api_id           = aws_apigatewayv2_api.virtual_me_api.id
  authorizer_type  = "REQUEST"
  authorizer_uri   = aws_lambda_function.authorizer.invoke_arn
  identity_sources = ["$request.header.Authorization"]
  name             = "lambda-authorizer"
}

# Or use Cognito
resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id          = aws_apigatewayv2_api.virtual_me_api.id
  authorizer_type = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name            = "cognito-authorizer"

  jwt_configuration {
    audience = [aws_cognito_user_pool_client.client.id]
    issuer   = "https://cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.pool.id}"
  }
}
```

### 2. API Rate Limiting

**AWS WAF Rule**:

```hcl
resource "aws_wafv2_web_acl" "api_protection" {
  name  = "virtual-me-api-protection"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "rate-limit"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 100  # requests per 5 minutes
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "rate-limit-rule"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "api-protection"
    sampled_requests_enabled   = true
  }
}
```

### 3. Secrets Management

**Current**: Environment variables

**Production**: AWS Secrets Manager

```python
import boto3
import json

def get_openai_key():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='virtualme/openai')
    return json.loads(response['SecretString'])['api_key']

# Use in Lambda
openai_api_key = get_openai_key()
```

**Terraform**:

```hcl
resource "aws_secretsmanager_secret" "openai_key" {
  name = "virtualme/openai"
}

resource "aws_secretsmanager_secret_version" "openai_key" {
  secret_id     = aws_secretsmanager_secret.openai_key.id
  secret_string = jsonencode({
    api_key = var.openai_api_key
  })
}

# Grant Lambda access
resource "aws_iam_role_policy" "secrets_access" {
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["secretsmanager:GetSecretValue"]
      Resource = aws_secretsmanager_secret.openai_key.arn
    }]
  })
}
```

### 4. Input Validation

**Prevent Prompt Injection**:

```python
def sanitize_input(text: str, max_length: int = 500) -> str:
    # Remove potential prompt injection attempts
    dangerous_patterns = [
        "ignore previous instructions",
        "system:",
        "assistant:",
        "<|endoftext|>",
    ]

    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if pattern in text_lower:
            raise ValueError("Invalid input detected")

    # Truncate to max length
    return text[:max_length]

# Use in Lambda
try:
    question = sanitize_input(last_user_message)
except ValueError:
    return http_response(400, {'error': 'Invalid input'})
```

## Scaling Considerations

### Horizontal Scaling

**Lambda Auto-Scaling**:
- Default concurrency limit: 1000 (per region)
- Can request increase to 10,000+
- Each container handles 1 request at a time

**Cost at Scale**:
- 1M requests/day
- Avg duration: 1 second
- Memory: 512 MB

```
Lambda cost = (1M requests × $0.20/1M) + (1M seconds × 512MB/1024 × $0.0000166667)
            = $0.20 + $8.33
            = $8.53/day
            = $256/month
```

### Database-Backed Vector Store

**When to migrate**:
- Resume size > 1 MB
- Need to update knowledge base without redeploying
- Multiple users with different knowledge bases

**Migration to Pinecone**:

```python
from langchain_pinecone import PineconeVectorStore

# Initialize Pinecone
vectorstore = PineconeVectorStore.from_documents(
    documents=splits,
    embedding=OpenAIEmbeddings(),
    index_name="virtual-me",
    namespace=user_id  # Multi-tenancy
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
```

### Multi-Tenancy Architecture

```
┌─────────────────────────────────┐
│  API Gateway                    │
│  + Lambda Authorizer            │
│  (extracts user_id from JWT)    │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Lambda Function                │
│  - Receives user_id from event  │
│  - Loads user-specific resume   │
│  from S3/DynamoDB               │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Pinecone Vector Store          │
│  - Namespace per user           │
│  - Isolated data                │
└─────────────────────────────────┘
```

---

**Last Updated**: 2024
**Version**: 1.0
**Author**: Virtual Me Team
