# Virtual Me - Technical Deep Dive

## 1. Request/Response Flow with JSON Examples

Here is the complete end-to-end flow from user input to AI response, including actual JSON payloads exchanged between components, CORS handling, validation, RAG pipeline execution, and error cases.

### Request Flow Diagram

```
User Input
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. Web UI (Deep Chat)                                       │
│    POST https://api.lemaire.tel/chat                        │
│    Content-Type: application/json                           │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Route 53                                                  │
│    DNS: api.lemaire.tel → API Gateway Endpoint              │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. API Gateway HTTP API                                      │
│    Transforms HTTP → Lambda Event (API Gateway v2 format)   │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Lambda (lambda_function.py)                               │
│    - Validates with Pydantic (ChatRequest)                  │
│    - Truncates to last 20 messages                          │
│    - Invokes run_rag_pipeline(question)                     │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. LangGraph Workflow (rag/pipeline.py)                      │
│    ┌──────────────┐      ┌──────────────┐                  │
│    │ retrieve_node│ ───► │ generate_node│                  │
│    └──────────────┘      └──────────────┘                  │
│           │                      │                          │
│           ↓                      ↓                          │
│      DynamoDB              Amazon Bedrock                   │
└─────────────────────────────────────────────────────────────┘
    ↓
Response (reverse path)
```

### CORS Preflight Handling

Before the actual POST request, browsers send a preflight OPTIONS request when making cross-origin calls (`chat.lemaire.tel` → `api.lemaire.tel`). The Lambda function explicitly returns 200 OK with CORS headers to allow the request:

```python
# lambda_function.py handles OPTIONS preflight
if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "https://chat.lemaire.tel",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "content-type"
        }
    }
```

### Step 1: Web UI Request (Deep Chat Format)

The Deep Chat UI sends a JSON payload with the conversation history:

```json
{
  "messages": [
    {
      "role": "user",
      "text": "What is your experience with AWS?"
    }
  ]
}
```

For conversations with history:

```json
{
  "messages": [
    {
      "role": "user",
      "text": "What technologies do you work with?"
    },
    {
      "role": "ai",
      "text": "I work with Python, AWS Lambda, Terraform, and Amazon Bedrock..."
    },
    {
      "role": "user",
      "text": "Tell me more about your AWS experience"
    }
  ]
}
```

### Step 2: API Gateway Event (Lambda Input)

API Gateway transforms the HTTP request into a Lambda event (AWS API Gateway v2 format):

```json
{
  "version": "2.0",
  "routeKey": "POST /chat",
  "rawPath": "/chat",
  "requestContext": {
    "accountId": "123456789012",
    "apiId": "abc123xyz",
    "domainName": "api.lemaire.tel",
    "requestId": "abc-123-def-456",
    "http": {
      "method": "POST",
      "path": "/chat",
      "protocol": "HTTP/1.1",
      "sourceIp": "203.0.113.42",
      "userAgent": "Mozilla/5.0..."
    },
    "time": "10/Jan/2026:14:23:45 +0000",
    "timeEpoch": 1736517825000
  },
  "headers": {
    "content-type": "application/json",
    "host": "api.lemaire.tel",
    "origin": "https://chat.lemaire.tel"
  },
  "body": "{\"messages\":[{\"role\":\"user\",\"text\":\"What is your experience with AWS?\"}]}",
  "isBase64Encoded": false
}
```

### Step 3: Lambda Processing

**Lambda validates, truncates, and extracts the request:**

```python
# lambda_function.py
body = json.loads(event.get("body", "{}"))

# Validation: Pydantic ensures schema validity. Malformed requests fail early.
chat_request = ChatRequest(**body)

# Truncation: Only last 20 messages retained to limit token usage and costs.
# Older context is irrelevant for immediate queries.
messages = chat_request.messages
if len(messages) > 20:
    messages = messages[-20:]

# Extract question and invoke RAG pipeline
question = messages[-1].text
answer = run_rag_pipeline(question)  # Invokes LangGraph workflow
```

### Step 4: LangGraph Internal State

**The RAG pipeline (`rag/pipeline.py`) implements a LangGraph state machine with two nodes:**
- `retrieve_node`: Calls DynamoDBRetriever, fetches chunks, flattens to context string
- `generate_node`: Injects context into System Prompt, calls Bedrock

**State flows through the workflow:**

**Initial State (after retrieve_node):**
```python
{
  "question": "What is your experience with AWS?",
  "context": "Jeremy Lemaire\n\nAWS Solutions Architect with 8 years of experience...\n\n---\n\nExpertise:\n- AWS Lambda, API Gateway, DynamoDB...\n\n---\n\nCertifications:\n- AWS Certified Solutions Architect Professional",
  "messages": [
    HumanMessage(content="You are a helpful assistant representing Jeremy..."),
    HumanMessage(content="What is your experience with AWS?")
  ]
}
```

**After generate_node:**
```python
{
  "question": "What is your experience with AWS?",
  "context": "...",  # Same as before
  "messages": [
    HumanMessage(content="You are a helpful assistant..."),
    HumanMessage(content="What is your experience with AWS?"),
    AIMessage(content="I have 8 years of experience as an AWS Solutions Architect...")
  ]
}
```

### Step 5: DynamoDB Query (Internal)

**Retrieve Node searches DynamoDB:**

The embedding for "What is your experience with AWS?" is computed:
```python
query_embedding = [0.123, -0.456, 0.789, ...]  # 1024-dimensional vector
```

DynamoDB scan retrieves all items and computes cosine similarity client-side:
```python
# Results sorted by similarity score
[
  {
    "id": "doc_0_abc123",
    "text": "Jeremy Lemaire\n\nAWS Solutions Architect with 2 years...",
    "similarity": 0.87
  },
  {
    "id": "doc_3_def456",
    "text": "Certifications:\n- AWS Certified Solutions Architect...",
    "similarity": 0.82
  },
  {
    "id": "doc_1_ghi789",
    "text": "Technical Skills:\n- Python, Terraform, AWS Lambda...",
    "similarity": 0.78
  }
]
# Top 3 are concatenated into the context string
```

### Step 6: Bedrock API Call (Internal)

**Generate Node calls Amazon Bedrock:**

```json
{
  "modelId": "us.amazon.nova-lite-v2:0",
  "messages": [
    {
      "role": "user",
      "content": "You are a Virtual Clone representing Jeremy Lemaire. Answer ONLY using information from the CONTEXT below.\n\nCONTEXT:\nJeremy Lemaire\n\nAWS Solutions Architect with 2 years of experience...\n\n---\n\nCertifications:\n- AWS Certified Solutions Architect Professional"
    },
    {
      "role": "user",
      "content": "What is your experience with AWS?"
    }
  ],
  "inferenceConfig": {
    "temperature": 0.1,
    "maxTokens": 500
  }
}
```

**Bedrock Response:**
```json
{
  "output": {
    "message": {
      "role": "assistant",
      "content": [
        {
          "text": "I have 2 years of experience as an AWS Solutions Architect. I specialize in serverless architectures using services like Lambda, API Gateway, and DynamoDB. I hold the AWS Certified Solutions Architect Professional certification."
        }
      ]
    }
  },
  "usage": {
    "inputTokens": 234,
    "outputTokens": 47,
    "totalTokens": 281
  }
}
```

### Step 7: Lambda Response (to API Gateway)

Lambda returns the response in the format expected by API Gateway v2:

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "https://chat.lemaire.tel",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "content-type"
  },
  "body": "{\"text\":\"I have 2 years of experience as an AWS Solutions Architect. I specialize in serverless architectures using services like Lambda, API Gateway, and DynamoDB. I hold the AWS Certified Solutions Architect Professional certification.\"}"
}
```

### Step 8: HTTP Response (to Web UI)

API Gateway transforms the Lambda response into an HTTP response:

```http
HTTP/1.1 200 OK
Content-Type: application/json
Access-Control-Allow-Origin: https://chat.lemaire.tel
Content-Length: 234

{
  "text": "I have 2 years of experience as an AWS Solutions Architect. I specialize in serverless architectures using services like Lambda, API Gateway, and DynamoDB. I hold the AWS Certified Solutions Architect Professional certification."
}
```

The Deep Chat UI receives this and displays the `text` field as the AI's response.

### Error Response Examples

**Validation Error (422 Unprocessable Entity):**

When the request body is malformed:

```json
{
  "statusCode": 422,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"error\":\"Validation failed\",\"details\":[{\"loc\":[\"messages\",0,\"role\"],\"msg\":\"Input should be 'user' or 'ai'\",\"type\":\"enum\"}]}"
}
```

**Bedrock Throttling (503 Service Unavailable):**

When Bedrock rate limits are exceeded:

```json
{
  "statusCode": 503,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"error\":\"Service temporarily unavailable\",\"message\":\"ThrottlingException: Rate exceeded\"}"
}
```

**Internal Error (500):**

When an unexpected error occurs:

```json
{
  "statusCode": 500,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"error\":\"Internal server error\",\"message\":\"An unexpected error occurred\"}"
}
```

---

## 2. Architecture & Lifecycle: Cold vs Warm Start

### Cold Start (~4 seconds)
Occurs when no active container exists (after ~15 mins inactivity).
1. **Python Imports**: `import langchain` (~1.5s).
2. **Module Level Initialization**:
   ```python
   # src/rag/dynamodb_retriever.py
   _vector_store = None  # Storage for global singleton
   ```
3. **Handler Execution**:
   - Calls `get_retriever()`.
   - Detects `_vector_store is None`.
   - **Initialization**: Establishes DynamoDB connection (SSL handshake ~0.5s), compiles graph (~0.5s).
   - **Total Latency**: ~4s (Source: AWS CloudWatch Logs `Report` lines showing `Init Duration`).

### Warm Start (<400ms)
Occurs on subsequent requests to the same container.
1. **Container State**: Memory preserved.
2. **No Imports**: Modules already loaded.
3. **Persisted Globals**: `_vector_store` already initialized.
   ```python
   def get_retriever():
       global _vector_store
       if _vector_store:
           return _vector_store  # Immediate return
   ```
4. **Execution**: Direct `graph.invoke()`.
   - Runtime limited to API I/O: ~20ms DynamoDB scan + ~300ms Bedrock generation.
   - **Source**: AWS X-Ray traces showing distinct subsegments for `DynamoDB` and `Bedrock`.

**Optimization**: Module-level global variables reuse connections across invocations.

---

## 3. Technical Key Points

### DynamoDB and GSI
Vector search requires comparing the query against **every single document** to determine semantic proximity.
- **Global Secondary Index (GSI)**: A sorted index. Cannot allow sorting by unrestricted semantic similarity.
- **Implementation**: **Full Table Scan**.
- **Process**: Loads all 50 chunks into memory (~10ms) and computes cosine similarity in Python.
- **Scalability**: Effective up to ~1000 chunks.
    *   **Source**: Latency budget math. 1000 chunks × 4KB = 4MB data. DynamoDB scans 1MB per request. = 4 round-trips to AWS storage (~60ms) + Python cosine calculation loop (~40ms) = ~100ms overhead. Beyond this, latency impacts user experience.
    *   **Alternative**: For >1000 chunks, use **[Approximate Nearest Neighbor (ANN)](https://en.wikipedia.org/wiki/Nearest_neighbor_search#Approximate_nearest_neighbor)** algorithms via tools like **AWS OpenSearch Service**, **ChromaDB**, or **PostgreSQL with pgvector**.
        *   **Why O(N)?**: Our current Full Scan compares the query against *every single document* (N). If data doubles, latency doubles.
        *   **How ANN fixes it**: Instead of checking everyone, ANN uses graph-based indexes to navigate only to "likely" neighbors, reducing search from 100% of rows to a slight fraction **O(log n)**.


### Binary Embedding Optimization
Embeddings are typically lists of **1024 floats** (the default for Titan V2).
```json
[0.123456789, 0.23456789, ...] // JSON representation ≈ 12KB per row
```
**Optimization**: Packed into binary using `struct.pack`.
- Standard float is 4 bytes. 1024 * 4 = **4KB**.
- **Result**: 3x reduction in storage size and read throughput costs.
- **Impact**: Negligible for current scale (50 rows), but significant for large-scale implementations (e.g., 1M rows saves ~8GB).

### Two HumanMessages Pattern
Certain models (e.g., Llama via specific adapters) fail when receiving a `SystemMessage` or strict role structures.
**Workaround implemented**:
1. `HumanMessage`: "System Prompt: You are a helpful assistant..."
2. `HumanMessage`: "Question: ..."

The LLM processes the sequence as text completion. Ensures compatibility across Bedrock/OpenAI models without capability flags.

### LangGraph vs LangChain: The Transparency Shift

**LangChain (The "Magic" Way)**
Uses overridden operators (`|`) to hide logic. Difficult to debug due to implicit state passing.
```python
# Hidden state flow, opaque execution
chain = retriever | prompt | llm | parser
result = chain.invoke("question")
```

**LangGraph (Implemented Approach)**
Utilizes standard Python functions and explicit state definitions.
```python
# Clearly defined state schema
class GraphState(TypedDict):
    question: str
    context: str
    messages: List[BaseMessage]

# Pure function nodes
def retrieve(state):
    # Logic is visible and debuggable
    docs = retriever.get_relevant_documents(state["question"])
    return {"context": format_docs(docs)}

def generate(state):
    # Explicit data dependency
    response = llm.invoke(prompt.format(context=state["context"]))
    return {"messages": [response]}

# Explicit control flow
workflow.add_edge("retrieve", "generate")
```
**Advantage**: Provides full visibility into data transformations at every step, enabling easier debugging and customization.

### Bedrock Configuration
**Amazon Bedrock** is a fully managed service offering multiple foundation models (FMs) via a single API.
*   **Benefit**: Eliminates infrastructure management (no GPUs to provision) and allows hot-swapping models (e.g., Nova to Claude) purely via configuration.

- **Model**: `nova-2-lite` (optimized for cost/speed).
- **Temperature**: `0.1` (deterministic, fact-based output).
- **Throttling**: Automatically handled by `boto3`. We just set `mode='adaptive'` and the SDK manages backoff for us (see *Production Engineering*).

---

## 4. Few performance tricks

### L1 Cold Start Optimization (Execution Environment)
Strictly speaking, "Cold Start" (full process initialization) only occurs when AWS creates a **new Execution Environment**. This happens on the first request or after ~15 minutes of inactivity.
AWS uses **Firecracker** (a micro-VM technology) to create these isolated environments. While often called "containers" as a shorthand, they are technically lightweight VMs.
Once created, the environment is frozen and reused. We exploit this by using global variables to persist state.

**Implementation**:
```python
# src/rag/dynamodb_retriever.py
_vector_store = None

# Called on EVERY request
def get_vector_store():
    global _vector_store
    # The check below finds the variable is NOT None on warm starts
    if _vector_store is None:
        # EXPENSIVE: Runs only when a new environment is created (~4s)
        # Includes: SSL handshake, DynamoDB connection, graph compilation
        _vector_store = DynamoDBVectorStore(...)
    return _vector_store
```

### Context Sliding Window
We avoid "Unbounded History" which leads to **Token Explosion**.
*The Problem*: If we send 100 messages of history, the 101st request pays for processing all 100 previous turns. Costs grow linearly, and we unnecessarily fill the context window.

**Implementation**:
```python
# src/lambda_function.py
class ChatRequest(BaseModel):
    messages: List[Message]
    # Pydantic validation ensures structure before we even touch logic

def lambda_handler(event, context):
    # ... validation ...
    
    # SLIDING WINDOW: Strict Cap
    if len(messages) > CONVERSATION_TRUNCATE_LIMIT:
        messages = messages[-CONVERSATION_TRUNCATE_LIMIT:]
    
    # Deterministic cost ceiling.
    # Max cost per turn = (20 msgs * avg_tokens) + new_query
```

### RAG Hyperparameters
These are not random; they are tuned for "Resume QA".

#### Top K = 3 (The Sweet Spot Zone)
*   **Why not 1? (Misses Context)**: Markdown splitting often separates headers from content.
    *   *Scenario*: Chunk 1 has `## Experience`. Chunk 2 has `### Company A`.
    *   If we only retrieve Chunk 2, the LLM doesn't know it's "Experience". Retrieving 3 ensures we likely capture the surrounding semantic hierarchy.
*   **Why not 10? (Dilutes Signal)**:
    *   *Signal-to-Noise Ratio*: If only 1 chunk has the answer, adding 9 irrelevant chunks forces the LLM to process more tokens, increasing the chance it focuses on the wrong details ("finding a needle in a larger haystack").
    *   *Lost in the Middle*: LLMs are known to ignore information buried in the middle of a large context block.
    *   *Cost*: 10 chunks = 3x more input tokens than 3.

#### Temperature = 0.1
*   **Goal**: Determinism.
*   **Logic**: We want the LLM to act as a **Retrieval Engine**, not a Creative Writer.
    *   `0.1`: "According to the text, Jeremy studied AWS." (Fact)
    *   `0.9`: "Jeremy, a cloud wizard, soared through the AWS skies..." (Hallucination risk)

### AWS Adaptive Retries
Standard retries (fixed interval) often worsen specific AWS throttling scenarios (Thundering Herd problem).
Implemented `mode='adaptive'` provided by `botocore` to dynamically adjust backoff based on the endpoint's current load.

**Implementation**:
```python
# src/rag/generator.py
from botocore.config import Config

BEDROCK_RETRY_CONFIG = Config(
    retries={
        'max_attempts': 3,
        'mode': 'adaptive'  # Dynamic backoff for throttling (HTTP 429)
    }
)
```

### AWS X-Ray Tracing

X-Ray provides distributed tracing showing latency breakdowns for Lambda execution, DynamoDB queries, and Bedrock API calls.

**Current Implementation (Lambda X-Ray Enabled)**:
```hcl
# terraform/main.tf
resource "aws_lambda_function" "virtual_me" {
  tracing_config {
    mode = "Active"  # ✅ Enabled
  }
}
```

With Lambda X-Ray enabled, you automatically get traces for:
- Lambda execution time and cold starts
- **DynamoDB operations** (Scan queries with latency)
- **Bedrock API calls** (InvokeModel with token counts and latency)
- All boto3 SDK calls

**No Python SDK required** - Lambda's X-Ray integration automatically instruments boto3 calls.

**API Gateway Limitation**:

For **HTTP API (v2)** has been used  instead of REST API (v1) because:
- **70% cheaper**: $1.00/million vs $3.50/million requests
- **Simpler CORS**: Native configuration vs manual OPTIONS handling
- **Sufficient for this use case**: Simple POST endpoint with no need for API keys or usage plans

Trade-off: HTTP API v2 does **not support X-Ray tracing**. Only Lambda traces are captured.
---

## 5. Resource Utilization

### Lambda Memory Breakdown (512MB)
The function is configured with **512MB of RAM**. This is a deliberate choice based on actual utilization:

- **Python Runtime + Boto3**: ~120MB
- **LangChain + Dependencies**: ~180MB
- **Graph Compilation & Working State**: ~50MB
- **Total Overhead**: ~350MB
- **Safety Margin**: ~160MB (needed for embedding processing and JSON overhead).

Using less than 512MB often leads to `Memory Limit Exceeded` during the heavy initialization of LangChain and Bedrock clients.

---

## 6. Data Storage Strategy

### DynamoDB Schema (What we store)
We store the **Original Text** alongside the **Vector**. There is no "reverse engineering" of vectors back to text; we simply retrieve the text field that sits next to the winning vector.

**Item Structure**:
```json
{
  "id": "doc_0_abc123",              # Unique ID
  "text": "I have 8 years...",       # <--- The Payload (Retrieved & sent to LLM)
  "embedding": <Binary Blob>,        # <--- The Search Key (Used for math)
  "metadata": "{\"source\": \"...\"}"
}
```

### DynamoDB vs Dedicated Vector DB
Why does this architecture differ from using specialized tools like Chroma?

| Feature | DynamoDB (Our Approach) | Vector DB (e.g. Chroma) |
| :--- | :--- | :--- |
| **Storage** | Text + Vector in same row | Text + Vector in same row (Text stored as metadata) |
| **Search Logic** | **Client-Side (Python)**. We fetch EVERYTHING and loop through it to calculate cosine similarity. | **Server-Side**. The DB engine finds the nearest neighbors and returns the **Text** (we ignore the returned vector). |
| **Scalability** | **O(N)**. Slower as data grows. | **O(log n)**. Instant even with millions of rows. |
| **Cost** | High read cost (pay to read every row). | Optimized for search. |

**Why we chose DynamoDB**: It acts as a **'Serverless Poor Man's Vector DB'**. For <1000 items, brute-force scanning is practically free and requires zero maintenance, avoiding the complexity and cost of running a dedicated ElasticSearch/OpenSearch cluster (often $hundreds/month).

---

## 7. Summary
**Serverless RAG Architecture**
- **Compute**: Lambda (pay-per-request).
- **Storage**: DynamoDB (pay-per-request).
- **Inference**: Bedrock (pay-per-token).
- **Idle Cost**: $0.

Optimizes for low maintenance and zero baseline cost, eliminating the need for always-on container orchestration.
