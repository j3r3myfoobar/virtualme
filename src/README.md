# Source Code Structure

This directory contains the refactored Lambda function code organized into logical modules.

## 📁 Directory Structure

```
src/
├── lambda_function.py      # Entry point (Lambda handler)
├── resume.md              # Knowledge base
├── rag/                   # RAG pipeline modules
│   ├── __init__.py
│   ├── pipeline.py        # LangGraph orchestration
│   ├── retriever.py       # FAISS vector search
│   ├── generator.py       # LLM response generation
│   └── state.py           # LangGraph state definition
├── loaders/               # Document loaders
│   ├── __init__.py
│   └── knowledge_base.py  # Resume loading & splitting
└── utils/                 # Utility functions
    ├── __init__.py
    └── http.py            # HTTP response formatting
```

## 🎯 Module Responsibilities

### lambda_function.py
**Main entry point** for AWS Lambda

- Handles HTTP events from API Gateway
- Extracts user messages
- Delegates to RAG pipeline
- Returns formatted HTTP responses

**Key functions:**
- `lambda_handler(event, context)` - AWS Lambda handler
- `extract_last_user_message(messages)` - Message extraction

### rag/pipeline.py
**Orchestrates the RAG workflow** using LangGraph

- Defines the retrieve → generate workflow
- Coordinates retriever and generator
- Formats final responses

**Key functions:**
- `run_rag_pipeline(question)` - Main entry point
- `retrieve_node(state)` - Retrieval step
- `generate_node(state)` - Generation step
- `build_graph()` - Constructs LangGraph workflow

### rag/retriever.py
**FAISS-based semantic search with multi-backend embeddings**

- Loads knowledge base documents
- Creates embeddings (Bedrock Titan or OpenAI)
- Builds FAISS index
- Performs similarity search

**Key functions:**
- `get_retriever(top_k=3)` - Get/create retriever
- `reset_retriever()` - Clear cache

**Cold start optimization:**
- Caches retriever in module-level variable
- Only builds index once per container

**Supported backends:**
- Bedrock Titan Embeddings (production)
- OpenAI Embeddings (optional)

### rag/generator.py
**LLM-based response generation with multi-backend support**

- Calls Bedrock (Llama, Claude), LM Studio, or OpenAI
- Enforces grounding in context
- Manages system prompts

**Key functions:**
- `generate_response(context, question)` - Generate answer
- `update_system_prompt(new_prompt)` - Customize behavior

**Supported backends:**
- Bedrock: Llama 3.2 (1B, 3B, 8B), Claude 3 Haiku, Mistral 7B
- LM Studio: Any local model
- OpenAI: GPT-4o-mini, GPT-4o (legacy)

**Configuration:**
- Backend: Set via `LLM_BACKEND` env var
- Model: Set via `LLM_MODEL` env var
- Temperature: `0.3` (low for factual responses)

### rag/state.py
**LangGraph state definition**

- Defines `GraphState` TypedDict
- Used by all LangGraph nodes

### loaders/knowledge_base.py
**Document loading and splitting**

- Reads `resume.md`
- Splits by markdown headers
- Maintains hierarchical context

**Key functions:**
- `load_knowledge_base()` - Load and split documents

### utils/http.py
**HTTP response utilities**

- Formats API Gateway responses
- Adds CORS headers

**Key functions:**
- `http_response(status_code, body)` - Format response

## 🔧 Usage Examples

### Running Locally with LM Studio

```bash
# From project root
cd src

# Configure environment (create .env file)
cat > .env << EOF
LLM_BACKEND=lm_studio
LLM_MODEL=llama-3.2-3b-instruct
LLM_TEMPERATURE=0.3
EMBEDDING_BACKEND=bedrock
EMBEDDING_MODEL=titan-embed-text-v2
AWS_REGION=us-east-1
EOF

# Run
python lambda_function.py
```

### Running Locally with Bedrock

```bash
# Ensure AWS credentials are configured
aws configure

# Set environment variables
export LLM_BACKEND=bedrock
export LLM_MODEL=llama-3.2-3b
export EMBEDDING_BACKEND=bedrock
export EMBEDDING_MODEL=titan-embed-text-v2

# Run
python lambda_function.py
```

### Importing Modules

```python
# In Python code
from rag.pipeline import run_rag_pipeline
from utils.http import http_response

# Run RAG pipeline
answer = run_rag_pipeline("What is your experience?")

# Format HTTP response
response = http_response(200, {'text': answer})
```

### Customizing RAG Parameters

```python
import os
from rag.retriever import get_retriever
from rag.generator import generate_response, update_system_prompt

# Switch models via environment
os.environ["LLM_MODEL"] = "claude-3-haiku"  # Use Claude instead of Llama

# Get retriever with more results
retriever = get_retriever(top_k=5)

# Customize system prompt
update_system_prompt("""
You are a friendly assistant...
CONTEXT: {context}
""")
```

### Backend Configuration

```python
from config import get_model_config, BEDROCK_MODELS

# Get current config
config = get_model_config()
print(f"Backend: {config.backend}")
print(f"Model: {config.model_id}")

# List available Bedrock models
print("Available models:")
for name, model_id in BEDROCK_MODELS.items():
    print(f"  - {name}: {model_id}")
```

## 🧪 Testing

```bash
# Run all unit tests
python tests/test_all.py

# Run specific test suite
python tests/unit/test_http.py
python tests/unit/test_knowledge_base.py
python tests/unit/test_lambda_handler.py
```

## 📦 Deployment

The deployment scripts automatically package all modules:

```bash
# LocalStack
./scripts/localstack-deploy.sh

# AWS
cd terraform && terraform apply
```

**Package contents:**
```
deployment.zip
├── lambda_function.py
├── resume.md
├── rag/
│   ├── __init__.py
│   ├── pipeline.py
│   ├── retriever.py
│   ├── generator.py
│   └── state.py
├── loaders/
│   ├── __init__.py
│   └── knowledge_base.py
├── utils/
│   ├── __init__.py
│   └── http.py
└── [dependencies from requirements.txt]
```

## 🎨 Design Patterns

### Singleton Pattern
- **retriever.py**: Cached retriever instance
- **pipeline.py**: Cached LangGraph instance

### Separation of Concerns
- **Retrieval** logic isolated in `retriever.py`
- **Generation** logic isolated in `generator.py`
- **HTTP** logic isolated in `utils/http.py`

### Cold Start Optimization
- Module-level initialization
- Cached instances prevent rebuilding

## 🔄 Migration from Monolithic

**Old structure:**
```
src/lambda_function.py  (330 lines)
```

**New structure:**
```
src/
├── lambda_function.py     (~100 lines)
├── rag/pipeline.py        (~150 lines)
├── rag/retriever.py       (~80 lines)
├── rag/generator.py       (~100 lines)
├── rag/state.py           (~20 lines)
├── loaders/knowledge_base.py (~60 lines)
└── utils/http.py          (~30 lines)
```

**Benefits:**
- ✅ Easier to understand
- ✅ Easier to test
- ✅ Easier to maintain
- ✅ Easier to extend
- ✅ Same deployment (1 Lambda)

## 📝 Adding New Features

### Add a New Retriever

```python
# src/rag/retriever_custom.py
def get_custom_retriever():
    # Your implementation
    pass

# Update src/rag/__init__.py
from .retriever_custom import get_custom_retriever
```

### Add New Document Source

```python
# src/loaders/blog_posts.py
def load_blog_posts():
    # Load from database, API, etc.
    pass

# Use in retriever.py
from loaders.blog_posts import load_blog_posts
```

### Add Response Post-Processing

```python
# src/utils/formatting.py
def format_markdown(text):
    # Convert to markdown, add links, etc.
    pass

# Use in lambda_function.py
from utils.formatting import format_markdown
answer = format_markdown(raw_answer)
```

## 🐛 Debugging

### Enable Verbose Logging

```python
# In any module
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Individual Modules

```python
# Test retriever
from rag.retriever import get_retriever
retriever = get_retriever()
docs = retriever.get_relevant_documents("test query")
print(docs)

# Test generator
from rag.generator import generate_response
response = generate_response("context here", "question here")
print(response)
```

## 📚 Further Reading

- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FAISS Documentation](https://faiss.ai/)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
