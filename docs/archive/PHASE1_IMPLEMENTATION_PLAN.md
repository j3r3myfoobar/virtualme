# Phase 1: Production Readiness - Implementation Plan

**Goal**: Fix critical blockers preventing production deployment
**Timeline**: 3-4 days (~27 hours)
**Priority**: 🔴 Critical

---

## Tasks Overview

| # | Task | Effort | Priority | Status |
|---|------|--------|----------|--------|
| 1 | Fix dependency versions | 4h | 🔴 Critical | ⏳ In Progress |
| 2 | Add structured logging | 6h | 🔴 Critical | ⏸️ Pending |
| 3 | Add integration tests | 8h | 🔴 Critical | ⏸️ Pending |
| 4 | Add error recovery & retry | 4h | 🔴 Critical | ⏸️ Pending |
| 5 | Add request validation | 4h | 🔴 Critical | ⏸️ Pending |
| 6 | Move test files | 1h | 🟡 Medium | ⏸️ Pending |

---

## Task 1: Fix Dependency Versions (4h) 🔴

### Problem
- Using very old LangChain versions (0.1.0 from Jan 2024)
- Version conflicts: `langchain-core 1.0.7` incompatible with `langchain 0.1.0`
- Tests cannot run: `ModuleNotFoundError: No module named 'langchain_core.pydantic_v1'`

### Current Versions
```
langchain==0.1.0          ❌ Too old
langgraph==0.0.20         ❌ Too old
langchain-openai==0.0.2   ❌ Too old
langchain-aws==0.1.0      ❌ Too old (should be 0.2.x)
langchain-core==1.0.7     ⚠️ Too new (conflict)
```

### Target Versions
```
langchain==0.3.7          ✅ Latest stable
langchain-core==0.3.15    ✅ Compatible
langchain-community==0.3.7 ✅ Compatible
langgraph==0.2.45         ✅ Latest stable
langchain-aws==0.2.6      ✅ Latest stable
langchain-openai==0.2.8   ✅ Latest stable
```

### Implementation Steps

#### 1.1. Update requirements.txt
- [x] Create requirements-updated.txt with new versions
- [ ] Test compatibility locally
- [ ] Update requirements.txt
- [ ] Document breaking changes (if any)

#### 1.2. Test Compatibility
- [ ] Install new dependencies in clean environment
- [ ] Run existing unit tests
- [ ] Verify imports work
- [ ] Check for API changes in LangChain 0.3.x

#### 1.3. Fix Breaking Changes
Potential breaking changes in LangChain 0.3.x:
- Pydantic v1 → v2 migration
- LangGraph API changes
- ChatModel interface changes

Files to check:
- `src/rag/generator.py` - ChatModel usage
- `src/rag/retriever.py` - Embeddings usage
- `src/rag/pipeline.py` - LangGraph StateGraph
- `src/rag/state.py` - TypedDict definitions

#### 1.4. Validation
- [ ] Run `python test_bedrock_simple.py` - Should pass
- [ ] Run `python tests/test_all.py` - Should pass (9/9)
- [ ] Test imports work without errors

---

## Task 2: Add Structured Logging (6h) 🔴

### Problem
- Using `print()` statements everywhere
- Cannot debug production issues
- No log levels (INFO, WARNING, ERROR)
- No structured data for CloudWatch Insights

### Current State
```python
print(f"Processing question: {last_user_message[:100]}...")  # ❌
print(f"Response generated: {answer[:100]}...")              # ❌
print(f"Error processing request: {str(e)}")                 # ❌
```

### Target State
```python
logger.info("processing_question", extra={
    "question_length": len(question),
    "request_id": context.request_id
})
logger.error("llm_invocation_failed", extra={
    "error": str(e),
    "backend": config.backend
}, exc_info=True)
```

### Implementation Steps

#### 2.1. Create Logging Utility
**File**: `src/utils/logger.py`
```python
import logging
import json
import sys
from typing import Any, Dict

class StructuredLogger:
    """Structured JSON logger for CloudWatch."""

    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Use JSON formatter for CloudWatch
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

    def info(self, event: str, **kwargs):
        self.logger.info(json.dumps({"event": event, **kwargs}))

    def warning(self, event: str, **kwargs):
        self.logger.warning(json.dumps({"event": event, **kwargs}))

    def error(self, event: str, exc_info=False, **kwargs):
        self.logger.error(json.dumps({"event": event, **kwargs}), exc_info=exc_info)

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return record.getMessage()
```

#### 2.2. Update Files
Replace `print()` with structured logging:

**Files to update**:
1. `src/lambda_function.py` - Main handler
2. `src/rag/pipeline.py` - RAG workflow
3. `src/rag/generator.py` - LLM invocation
4. `src/rag/retriever.py` - FAISS retrieval

**Example changes**:
```python
# Before
print(f"Processing question: {last_user_message[:100]}...")

# After
logger.info("processing_question", extra={
    "question_preview": last_user_message[:100],
    "question_length": len(last_user_message),
    "request_id": context.request_id
})
```

#### 2.3. Add CloudWatch Metrics (Terraform)
**File**: `terraform/cloudwatch.tf` (new)
```hcl
resource "aws_cloudwatch_log_metric_filter" "errors" {
  name           = "lambda-errors"
  log_group_name = aws_cloudwatch_log_group.lambda.name
  pattern        = "[timestamp, request_id, level=ERROR, ...]"

  metric_transformation {
    name      = "ErrorCount"
    namespace = "VirtualMe"
    value     = "1"
  }
}
```

---

## Task 3: Add Integration Tests (8h) 🔴

### Problem
- Empty `tests/integration/` directory
- No end-to-end RAG pipeline tests
- Cannot verify Bedrock/LM Studio switching works
- No tests for error scenarios

### Implementation Steps

#### 3.1. Create Mock Backend
**File**: `tests/integration/mock_backend.py`
```python
class MockChatModel:
    """Mock LLM for testing."""
    def invoke(self, messages):
        return "Mock response based on context."

class MockEmbeddings:
    """Mock embeddings for testing."""
    def embed_documents(self, texts):
        return [[0.1] * 384 for _ in texts]
```

#### 3.2. Create Integration Tests
**File**: `tests/integration/test_rag_pipeline.py`

Tests to implement:
1. `test_rag_pipeline_end_to_end()` - Full pipeline with mock
2. `test_bedrock_backend_selection()` - Bedrock config
3. `test_lm_studio_backend_selection()` - LM Studio config
4. `test_empty_question_handling()` - Error case
5. `test_retrieval_accuracy()` - FAISS retrieves correct docs
6. `test_context_formatting()` - Context passed to LLM correctly
7. `test_lambda_handler_integration()` - Full Lambda flow

#### 3.3. Add Test Runner
**File**: `tests/integration/test_all_integration.py`
```python
import pytest
import os

def test_suite():
    """Run all integration tests."""
    os.environ['LLM_BACKEND'] = 'mock'
    pytest.main(['-v', 'tests/integration/'])
```

---

## Task 4: Add Error Recovery & Retry (4h) 🔴

### Problem
- No retry logic for Bedrock throttling
- No exponential backoff
- Network timeouts cause user-facing errors

### Implementation Steps

#### 4.1. Add Tenacity Dependency
Already in `requirements-updated.txt`:
```python
tenacity>=8.2.0
```

#### 4.2. Create Retry Wrapper
**File**: `src/utils/retry.py`
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import logging

logger = logging.getLogger(__name__)

def bedrock_retry(func):
    """Retry decorator for Bedrock API calls."""
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            Exception,  # Catch throttling, timeouts
        )),
        before_sleep=lambda retry_state: logger.warning(
            "bedrock_retry",
            attempt=retry_state.attempt_number,
            exception=str(retry_state.outcome.exception())
        )
    )(func)
```

#### 4.3. Update Generator
**File**: `src/rag/generator.py`
```python
from utils.retry import bedrock_retry

@bedrock_retry
def _invoke_llm(llm, messages):
    """Invoke LLM with retry logic."""
    return llm.invoke(messages)
```

#### 4.4. Update Retriever
Add retry for embedding generation (can also throttle).

---

## Task 5: Add Request Validation (4h) 🔴

### Problem
- Minimal input validation
- No type checking
- No length limits (abuse vector)
- Malformed requests can crash Lambda

### Implementation Steps

#### 5.1. Add Pydantic Models
**File**: `src/models/requests.py` (new)
```python
from pydantic import BaseModel, Field, validator
from typing import List, Literal

class Message(BaseModel):
    """Single message in conversation."""
    role: Literal["user", "ai"] = Field(..., description="Message role")
    text: str = Field(..., min_length=1, max_length=2000, description="Message text")

    @validator('text')
    def validate_text_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Message text cannot be empty")
        return v.strip()

class ChatRequest(BaseModel):
    """Chat request from frontend."""
    messages: List[Message] = Field(..., min_items=1, max_items=50)

    @validator('messages')
    def validate_last_message_is_user(cls, messages):
        if messages[-1].role != 'user':
            raise ValueError("Last message must be from user")
        return messages

class ChatResponse(BaseModel):
    """Chat response to frontend."""
    text: str = Field(..., min_length=1)
```

#### 5.2. Update Lambda Handler
**File**: `src/lambda_function.py`
```python
from models.requests import ChatRequest, ChatResponse
from pydantic import ValidationError

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))

        # Validate request
        try:
            request = ChatRequest(**body)
        except ValidationError as e:
            return http_response(422, {
                'error': 'Invalid request',
                'details': e.errors()
            })

        # Extract message
        last_message = request.messages[-1].text

        # Process...
```

---

## Task 6: Move Test Files (1h) 🟡

### Current Structure (Wrong)
```
/test_bedrock_setup.py          ❌
/test_bedrock_simple.py         ❌
/BEDROCK_INTEGRATION_PROOF.md   ❌
```

### Target Structure (Correct)
```
tests/
  integration/
    test_bedrock_setup.py       ✅
    test_bedrock_integration.py ✅
docs/
  bedrock-integration-proof.md  ✅
```

### Implementation
```bash
# Move test files
mkdir -p tests/integration
mv test_bedrock_setup.py tests/integration/
mv test_bedrock_simple.py tests/integration/test_bedrock_integration.py

# Move docs
mkdir -p docs
mv BEDROCK_INTEGRATION_PROOF.md docs/bedrock-integration-proof.md
mv SENIOR_ENGINEER_REVIEW.md docs/senior-engineer-review.md
```

---

## Testing Strategy

### After Each Task
1. Run unit tests: `python tests/test_all.py`
2. Run integration tests: `pytest tests/integration/`
3. Manual smoke test: `cd src && python lambda_function.py`

### Final Validation
1. All tests pass (unit + integration)
2. No dependency conflicts
3. Logging produces structured JSON
4. Retry logic works (can be tested with mocks)
5. Invalid requests return 422 errors
6. Clean project structure

---

## Rollback Plan

If anything breaks:
1. **Dependencies**: Revert requirements.txt to working version
2. **Code changes**: Each task is in separate commit, can cherry-pick
3. **Tests**: Keep old tests until new ones pass

---

## Success Criteria

✅ **Task 1**: Install new dependencies, all tests pass
✅ **Task 2**: Structured JSON logs in CloudWatch format
✅ **Task 3**: 7+ integration tests passing
✅ **Task 4**: Retry logic demonstrated with mocks
✅ **Task 5**: Invalid requests rejected with 422
✅ **Task 6**: Clean directory structure

**Overall Success**: All 6 tasks complete, project is production-ready for Phase 2.

---

## Next Steps (Phase 2)

After Phase 1 is complete:
1. Add response caching (DynamoDB)
2. Add monitoring & alerting (CloudWatch)
3. Set up CI/CD pipeline (GitHub Actions)
4. Add rate limiting (API Gateway)

---

**Start Date**: 2025-11-21
**Target Completion**: 2025-11-24 (3-4 days)
**Last Updated**: 2025-11-21
