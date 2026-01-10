"""
Pytest fixtures for Virtual Me chatbot tests.

Provides shared fixtures for mocking AWS services and test data.
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))


@pytest.fixture
def sample_embeddings():
    """Sample embedding vectors for testing similarity search."""
    return [
        [0.1, 0.2, 0.3, 0.4, 0.5],
        [0.2, 0.3, 0.4, 0.5, 0.6],
        [0.9, 0.8, 0.7, 0.6, 0.5],
    ]


@pytest.fixture
def sample_texts():
    """Sample document texts for testing."""
    return [
        "I have 8 years of experience in software engineering.",
        "I specialize in cloud architecture and serverless computing.",
        "I led a team of 5 engineers at Tech Innovations Inc.",
    ]


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table for testing vector store operations."""
    mock_table = MagicMock()
    mock_table.scan.return_value = {'Items': [], 'Count': 0}
    mock_table.batch_writer.return_value.__enter__ = MagicMock()
    mock_table.batch_writer.return_value.__exit__ = MagicMock()
    return mock_table


@pytest.fixture
def mock_bedrock_response():
    """Mock Bedrock LLM response for testing generator."""
    mock_response = MagicMock()
    mock_response.content = "I have 8 years of experience in software engineering, specializing in cloud architecture."
    return mock_response


@pytest.fixture
def mock_llm(mock_bedrock_response):
    """Mock LLM instance for testing."""
    mock = MagicMock()
    mock.invoke.return_value = mock_bedrock_response
    return mock


@pytest.fixture
def sample_context():
    """Sample context for testing generator."""
    return """## Professional Summary
Experienced Senior Software Engineer with 8+ years of expertise in cloud architecture,
serverless computing, and full-stack development.

## Technical Skills
- Cloud Platforms: AWS (Lambda, API Gateway, S3, DynamoDB)
- Programming Languages: Python, JavaScript/TypeScript"""


@pytest.fixture
def sample_question():
    """Sample question for testing."""
    return "What is your experience level?"
