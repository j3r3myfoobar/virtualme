# LangChain 0.1.0 → 0.3.7 Migration Guide

**Date**: 2025-11-21
**Reason**: Fix dependency conflicts and enable production readiness
**Impact**: Medium - Some API changes required

---

## Version Changes Summary

| Package | Old Version | New Version | Change |
|---------|-------------|-------------|--------|
| langchain | 0.1.0 | 0.3.7 | Major upgrade |
| langchain-core | (mixed) | 0.3.15 | Standardized |
| langchain-community | 0.0.20 | 0.3.7 | Major upgrade |
| langgraph | 0.0.20 | 0.2.45 | Major upgrade |
| langchain-aws | 0.1.0 | 0.2.6 | Minor upgrade |
| langchain-openai | 0.0.2 | 0.2.8 | Major upgrade |
| faiss-cpu | 1.7.4 | 1.8.0 | Minor upgrade |
| tiktoken | 0.5.2 | 0.8.0 | Minor upgrade |

**New dependencies**:
- `langchain-text-splitters==0.3.2` (text splitting extracted to separate package)
- `pydantic>=2.0.0` (Pydantic v2 support)
- `pydantic-settings>=2.0.0`
- `tenacity>=8.2.0` (for retry logic)

---

## Breaking Changes

### 1. Text Splitters Moved to Separate Package

**Old** (LangChain 0.1.0):
```python
from langchain.text_splitter import MarkdownHeaderTextSplitter
```

**New** (LangChain 0.3.7):
```python
from langchain_text_splitters import MarkdownHeaderTextSplitter
```

**Impact**: `src/loaders/knowledge_base.py`

**Fix Required**: ✅ Update import statement

---

### 2. Pydantic v1 → v2 Migration

**Old**:
```python
from langchain_core.pydantic_v1 import Field  # This caused the error!
```

**New**:
```python
from pydantic import Field, BaseModel
```

**Impact**: All code using Pydantic models

**Fix Required**: ✅ Update imports (LangChain 0.3.x uses Pydantic v2 natively)

---

### 3. LangGraph StateGraph API

**Potential Change**: StateGraph API may have minor changes

**Current Usage** (`src/rag/pipeline.py`):
```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(GraphState)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)
app = workflow.compile()
```

**Expected**: API should be backward compatible

**Action**: Test after upgrade

---

### 4. ChatModel Interface

**Potential Change**: ChatBedrock and ChatOpenAI APIs

**Current Usage** (`src/rag/generator.py`):
```python
from langchain_aws import ChatBedrock
from langchain_openai import ChatOpenAI

llm = ChatBedrock(model_id=..., region_name=..., model_kwargs={...})
response = llm.invoke(messages)
```

**Expected**: API should be backward compatible

**Action**: Test after upgrade

---

### 5. Embeddings Interface

**Current Usage** (`src/rag/retriever.py`):
```python
from langchain_aws import BedrockEmbeddings
from langchain_openai import OpenAIEmbeddings

embeddings = BedrockEmbeddings(model_id=..., region_name=...)
```

**Expected**: API should be backward compatible

**Action**: Test after upgrade

---

## Files Requiring Changes

### ✅ Confirmed Changes Required

1. **src/loaders/knowledge_base.py**
   - Update: `from langchain.text_splitter import` → `from langchain_text_splitters import`

### ⚠️ Potential Changes (Test Required)

2. **src/rag/pipeline.py**
   - Test: LangGraph StateGraph API
   - Test: END import

3. **src/rag/generator.py**
   - Test: ChatBedrock instantiation
   - Test: ChatOpenAI instantiation
   - Test: `.invoke()` method

4. **src/rag/retriever.py**
   - Test: BedrockEmbeddings instantiation
   - Test: OpenAIEmbeddings instantiation
   - Test: `.embed_documents()` and `.embed_query()` methods

5. **src/rag/state.py**
   - Test: TypedDict compatibility

---

## Testing Strategy

### Step 1: Install New Dependencies
```bash
# Create clean environment (optional but recommended)
python -m venv venv-test
source venv-test/bin/activate

# Install new requirements
pip install -r requirements.txt
```

### Step 2: Test Imports
```bash
python -c "
from langchain import LLMChain
from langchain_aws import ChatBedrock, BedrockEmbeddings
from langchain_openai import ChatOpenAI
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langgraph.graph import StateGraph, END
print('✓ All imports successful')
"
```

### Step 3: Run Unit Tests
```bash
python tests/test_all.py
```

Expected: 9/9 tests should pass (if not, fix the broken code)

### Step 4: Test Configuration System
```bash
cd src
python -c "
from config import get_model_config
config = get_model_config()
print(f'Config loaded: {config.backend} / {config.model_id}')
"
```

### Step 5: Manual Smoke Test
```bash
# Set environment
export LLM_BACKEND=bedrock
export LLM_MODEL=llama-3.2-3b

# Try to run (will fail without AWS creds, but should load modules)
cd src
python lambda_function.py
```

---

## Rollback Plan

If upgrade fails:
```bash
git checkout requirements.txt
pip install -r requirements.txt
```

Then investigate specific breaking changes.

---

## Benefits of Upgrade

### 1. Fixes Dependency Conflicts ✅
- Resolves `langchain_core.pydantic_v1` error
- Compatible versions across all packages

### 2. Pydantic v2 Support ✅
- Better performance
- Better validation
- Required for request validation (Phase 1 Task 5)

### 3. Latest Features ✅
- LangChain 0.3.x: Better streaming, improved error handling
- LangGraph 0.2.x: Enhanced state management
- LangChain-AWS 0.2.x: Latest Bedrock model support

### 4. Production Readiness ✅
- Stable, well-tested versions
- Active maintenance and security updates
- Better AWS Lambda compatibility

### 5. Enables Phase 1 Tasks ✅
- Structured logging works better with Pydantic v2
- Retry logic requires tenacity (now included)
- Request validation needs Pydantic v2

---

## Migration Checklist

- [x] Update requirements.txt
- [ ] Fix import in `src/loaders/knowledge_base.py`
- [ ] Test all modules load without errors
- [ ] Run unit tests (9/9 should pass)
- [ ] Run integration validation
- [ ] Commit changes
- [ ] Document any additional breaking changes found

---

## Next Steps After Migration

1. **Implement remaining Phase 1 tasks**:
   - Task 2: Add structured logging
   - Task 3: Add integration tests
   - Task 4: Add retry logic (tenacity now available!)
   - Task 5: Add request validation (Pydantic v2 ready!)
   - Task 6: Move test files

2. **Update documentation** if any API changes found

3. **Monitor production** after deployment for any issues

---

**Status**: ⏳ In Progress
**Risk Level**: 🟡 Medium (breaking changes expected but manageable)
**Estimated Fix Time**: 1-2 hours
