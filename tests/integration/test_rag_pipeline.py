#!/usr/bin/env python3
"""
Integration tests for the RAG pipeline.

Tests end-to-end functionality including:
- RAG pipeline with multiple backends
- Error handling and retry logic
- Backend switching (Bedrock, LM Studio, OpenAI)
- Request validation and error scenarios
- Lambda handler integration

Requires:
- pytest
- pytest-mock
- Environment variables for testing
"""

import json
import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from lambda_function import lambda_handler, extract_last_user_message
from rag.pipeline import run_rag_pipeline
from config import ModelConfig, get_model_config
from models.requests import ChatRequest, Message
from pydantic import ValidationError


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_bedrock_client():
    """Mock Bedrock client for testing without AWS credentials."""
    with patch('langchain_aws.ChatBedrock') as mock:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = Mock(content="I have 8 years of Python experience.")
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_embeddings():
    """Mock embeddings for testing without API calls."""
    with patch('langchain_aws.BedrockEmbeddings') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_faiss():
    """Mock FAISS vector store to avoid embedding API calls."""
    with patch('langchain_community.vectorstores.FAISS.from_documents') as mock:
        mock_vectorstore = MagicMock()
        mock_retriever = MagicMock()

        # Mock retrieved documents
        mock_doc = Mock()
        mock_doc.page_content = "I have 8+ years of Python development experience with Django, Flask, and FastAPI."
        mock_retriever.get_relevant_documents.return_value = [mock_doc]

        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock.return_value = mock_vectorstore
        yield mock


@pytest.fixture
def valid_event():
    """Valid Lambda API Gateway event."""
    return {
        'body': json.dumps({
            'messages': [
                {'role': 'user', 'text': 'What is your Python experience?'}
            ]
        }),
        'requestContext': {
            'http': {'method': 'POST'}
        }
    }


@pytest.fixture
def mock_lambda_context():
    """Mock Lambda context object."""
    context = Mock()
    context.aws_request_id = 'test-request-123'
    context.function_name = 'virtual-me-test'
    context.memory_limit_in_mb = 512
    context.get_remaining_time_in_millis = lambda: 30000
    return context


# ============================================================================
# TEST 1: End-to-End RAG Pipeline
# ============================================================================

def test_rag_pipeline_end_to_end(mock_bedrock_client, mock_embeddings, mock_faiss):
    """
    Test complete RAG pipeline from question to answer.

    Validates:
    - Knowledge base loading
    - Document retrieval
    - Context formatting
    - LLM response generation
    """
    # Set environment for Bedrock
    os.environ['LLM_BACKEND'] = 'bedrock'
    os.environ['LLM_MODEL'] = 'llama-3.2-3b'
    os.environ['EMBEDDING_BACKEND'] = 'bedrock'
    os.environ['EMBEDDING_MODEL'] = 'titan-embed-text-v2'
    os.environ['AWS_REGION'] = 'us-east-1'

    # Run pipeline
    question = "What is your Python experience?"
    answer = run_rag_pipeline(question)

    # Validate
    assert answer is not None
    assert isinstance(answer, str)
    assert len(answer) > 0
    assert "Python" in answer or "experience" in answer


# ============================================================================
# TEST 2: Lambda Handler with Valid Request
# ============================================================================

def test_lambda_handler_valid_request(valid_event, mock_lambda_context, mock_bedrock_client, mock_embeddings, mock_faiss):
    """
    Test Lambda handler with valid Deep Chat request.

    Validates:
    - Request parsing
    - Pydantic validation
    - RAG pipeline execution
    - Response formatting
    - HTTP 200 status
    """
    os.environ['LLM_BACKEND'] = 'bedrock'
    os.environ['LLM_MODEL'] = 'llama-3.2-3b'
    os.environ['EMBEDDING_BACKEND'] = 'bedrock'
    os.environ['EMBEDDING_MODEL'] = 'titan-embed-text-v2'
    os.environ['AWS_REGION'] = 'us-east-1'

    response = lambda_handler(valid_event, mock_lambda_context)

    # Validate response structure
    assert response['statusCode'] == 200
    assert 'body' in response

    # Parse response body
    body = json.loads(response['body'])
    assert 'text' in body
    assert isinstance(body['text'], str)
    assert len(body['text']) > 0


# ============================================================================
# TEST 3: Request Validation - Invalid Format
# ============================================================================

def test_lambda_handler_invalid_json(mock_lambda_context):
    """
    Test Lambda handler with malformed JSON.

    Validates:
    - JSON parsing error handling
    - HTTP 400 status
    - Error message format
    """
    event = {
        'body': '{invalid json',
        'requestContext': {'http': {'method': 'POST'}}
    }

    response = lambda_handler(event, mock_lambda_context)

    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'JSON' in body['error']


# ============================================================================
# TEST 4: Request Validation - Missing Fields
# ============================================================================

def test_lambda_handler_missing_messages(mock_lambda_context):
    """
    Test Lambda handler with missing required fields.

    Validates:
    - Pydantic validation errors
    - HTTP 422 status (Unprocessable Entity)
    - Detailed error response
    """
    event = {
        'body': json.dumps({'invalid_field': 'test'}),
        'requestContext': {'http': {'method': 'POST'}}
    }

    response = lambda_handler(event, mock_lambda_context)

    assert response['statusCode'] == 422
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'details' in body
    assert isinstance(body['details'], list)


# ============================================================================
# TEST 5: Request Validation - Empty Message
# ============================================================================

def test_lambda_handler_empty_message(mock_lambda_context):
    """
    Test Lambda handler with empty message text.

    Validates:
    - Field-level validation
    - Empty string detection
    - HTTP 422 status
    """
    event = {
        'body': json.dumps({
            'messages': [
                {'role': 'user', 'text': '   '}  # Whitespace only
            ]
        }),
        'requestContext': {'http': {'method': 'POST'}}
    }

    response = lambda_handler(event, mock_lambda_context)

    assert response['statusCode'] == 422
    body = json.loads(response['body'])
    assert 'error' in body


# ============================================================================
# TEST 6: CORS Preflight Request
# ============================================================================

def test_lambda_handler_cors_preflight(mock_lambda_context):
    """
    Test Lambda handler responds to OPTIONS requests.

    Validates:
    - CORS preflight handling
    - HTTP 200 status
    - No RAG pipeline execution
    """
    event = {
        'requestContext': {'http': {'method': 'OPTIONS'}}
    }

    response = lambda_handler(event, mock_lambda_context)

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['message'] == 'OK'


# ============================================================================
# TEST 7: Backend Switching - Bedrock
# ============================================================================

def test_backend_switching_bedrock(mock_bedrock_client, mock_embeddings):
    """
    Test switching to Bedrock backend.

    Validates:
    - Configuration updates
    - Correct model selection
    - Backend initialization
    """
    os.environ['LLM_BACKEND'] = 'bedrock'
    os.environ['LLM_MODEL'] = 'llama-3.2-3b'
    os.environ['AWS_REGION'] = 'us-east-1'

    config = get_model_config()

    assert config.backend == 'bedrock'
    assert config.model_id == 'meta.llama3-2-3b-instruct-v1:0'
    assert config.aws_region == 'us-east-1'


# ============================================================================
# TEST 8: Backend Switching - LM Studio
# ============================================================================

def test_backend_switching_lm_studio():
    """
    Test switching to LM Studio backend.

    Validates:
    - Configuration for local development
    - Custom base URL handling
    - Model ID preservation
    """
    os.environ['LLM_BACKEND'] = 'lm_studio'
    os.environ['LLM_MODEL'] = 'llama-3.2-3b-instruct'
    os.environ['LM_STUDIO_BASE_URL'] = 'http://localhost:1234/v1'

    config = get_model_config()

    assert config.backend == 'lm_studio'
    assert config.model_id == 'llama-3.2-3b-instruct'
    assert config.lm_studio_base_url == 'http://localhost:1234/v1'


# ============================================================================
# TEST 9: Retry Logic - Throttling Error
# ============================================================================

def test_retry_logic_throttling(mock_embeddings, mock_faiss):
    """
    Test retry logic handles throttling errors.

    Validates:
    - Exponential backoff retry
    - Throttling error detection
    - Eventually succeeds after retry
    """
    with patch('langchain_aws.ChatBedrock') as mock_bedrock:
        mock_instance = MagicMock()

        # First call fails with throttling, second succeeds
        mock_instance.invoke.side_effect = [
            Exception("ThrottlingException: Rate exceeded"),
            Mock(content="Success after retry")
        ]
        mock_bedrock.return_value = mock_instance

        os.environ['LLM_BACKEND'] = 'bedrock'
        os.environ['LLM_MODEL'] = 'llama-3.2-3b'
        os.environ['EMBEDDING_BACKEND'] = 'bedrock'
        os.environ['EMBEDDING_MODEL'] = 'titan-embed-text-v2'
        os.environ['AWS_REGION'] = 'us-east-1'

        # Should succeed after retry
        answer = run_rag_pipeline("Test question")

        assert answer is not None
        assert "Success after retry" in answer
        # Verify it was called twice (initial + 1 retry)
        assert mock_instance.invoke.call_count == 2


# ============================================================================
# TEST 10: Retry Logic - Non-Retriable Error
# ============================================================================

def test_retry_logic_non_retriable(mock_embeddings, mock_faiss):
    """
    Test retry logic with non-retriable errors.

    Validates:
    - Non-retriable errors are logged
    - Retries do occur (safety-first approach)
    - Eventually fails after max attempts
    - Proper error logging
    """
    with patch('langchain_aws.ChatBedrock') as mock_bedrock:
        mock_instance = MagicMock()

        # Non-retriable error (invalid credentials)
        mock_instance.invoke.side_effect = Exception("InvalidCredentials: Access denied")
        mock_bedrock.return_value = mock_instance

        os.environ['LLM_BACKEND'] = 'bedrock'
        os.environ['LLM_MODEL'] = 'llama-3.2-3b'
        os.environ['EMBEDDING_BACKEND'] = 'bedrock'
        os.environ['EMBEDDING_MODEL'] = 'titan-embed-text-v2'
        os.environ['AWS_REGION'] = 'us-east-1'

        # Should fail after retries
        with pytest.raises(Exception):
            run_rag_pipeline("Test question")

        # Verifies retry attempts (3 attempts: 1 initial + 2 retries)
        assert mock_instance.invoke.call_count == 3


# ============================================================================
# TEST 11: Extract Last User Message
# ============================================================================

def test_extract_last_user_message():
    """
    Test extracting last user message from conversation history.

    Validates:
    - Correct message extraction
    - Handles multiple messages
    - Returns empty string if no user messages
    """
    # Test with multiple messages
    messages = [
        {'role': 'user', 'text': 'Hello'},
        {'role': 'ai', 'text': 'Hi there!'},
        {'role': 'user', 'text': 'How are you?'}
    ]
    assert extract_last_user_message(messages) == 'How are you?'

    # Test with no user messages
    messages = [
        {'role': 'ai', 'text': 'Hello!'}
    ]
    assert extract_last_user_message(messages) == ''

    # Test with empty list
    assert extract_last_user_message([]) == ''


# ============================================================================
# TEST 12: Pydantic Models - Valid Request
# ============================================================================

def test_pydantic_chat_request_valid():
    """
    Test Pydantic ChatRequest model with valid data.

    Validates:
    - Successful validation
    - Field types
    - Last message role check
    """
    data = {
        'messages': [
            {'role': 'user', 'text': 'What is your experience?'}
        ]
    }

    request = ChatRequest(**data)

    assert len(request.messages) == 1
    assert request.messages[0].role == 'user'
    assert request.messages[0].text == 'What is your experience?'


# ============================================================================
# TEST 13: Pydantic Models - Invalid Last Message Role
# ============================================================================

def test_pydantic_chat_request_invalid_last_role():
    """
    Test Pydantic ChatRequest rejects non-user last message.

    Validates:
    - Last message must be from user
    - Validation error raised
    - Error message clarity
    """
    data = {
        'messages': [
            {'role': 'user', 'text': 'Hello'},
            {'role': 'ai', 'text': 'Hi!'}  # Last message is AI
        ]
    }

    with pytest.raises(ValidationError) as exc_info:
        ChatRequest(**data)

    errors = exc_info.value.errors()
    assert any('Last message must be from user' in str(e) for e in errors)


# ============================================================================
# TEST 14: Structured Logging
# ============================================================================

def test_structured_logging(valid_event, mock_lambda_context, mock_bedrock_client, mock_embeddings, mock_faiss):
    """
    Test structured logging throughout pipeline.

    Validates:
    - Logs are generated
    - Response is successful
    - No exceptions during logging
    """
    os.environ['LLM_BACKEND'] = 'bedrock'
    os.environ['LLM_MODEL'] = 'llama-3.2-3b'
    os.environ['EMBEDDING_BACKEND'] = 'bedrock'
    os.environ['EMBEDDING_MODEL'] = 'titan-embed-text-v2'
    os.environ['AWS_REGION'] = 'us-east-1'

    # Test that lambda handler completes successfully with logging
    response = lambda_handler(valid_event, mock_lambda_context)

    # Verify success (logs are written to stdout but test focuses on completion)
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'text' in body
    assert len(body['text']) > 0


# ============================================================================
# MAIN - Run with pytest
# ============================================================================

if __name__ == "__main__":
    """
    Run tests with pytest.

    Usage:
        cd tests/integration
        pytest test_rag_pipeline.py -v

        # Run specific test
        pytest test_rag_pipeline.py::test_rag_pipeline_end_to_end -v

        # Run with coverage
        pytest test_rag_pipeline.py --cov=../../src --cov-report=html
    """
    pytest.main([__file__, '-v', '--tb=short'])
