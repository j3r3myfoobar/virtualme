# Contributing to Virtual Me

Thank you for considering contributing to Virtual Me! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Guidelines](#testing-guidelines)
6. [Pull Request Process](#pull-request-process)
7. [Documentation](#documentation)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for everyone. Be respectful, constructive, and professional in all interactions.

### Expected Behavior

- Use welcoming and inclusive language
- Respect differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what's best for the community

## Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git
- OpenAI API key

### Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/virtualme.git
cd virtualme
git remote add upstream https://github.com/ORIGINAL_OWNER/virtualme.git
```

### Setup Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest black flake8 mypy

# Set up environment variables
cp .env.example .env
# Edit .env with your OpenAI API key
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming convention:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions or fixes

### 2. Make Your Changes

- Write clean, readable code
- Follow the coding standards below
- Add tests for new features
- Update documentation as needed

### 3. Test Locally

```bash
# Run tests
pytest

# Test with LocalStack
make localstack-deploy

# Validate code formatting
black --check .
flake8 .
mypy lambda_function.py
```

### 4. Commit Your Changes

Use conventional commit messages:

```bash
git commit -m "feat: add caching layer to RAG pipeline"
git commit -m "fix: resolve CORS issue in API Gateway"
git commit -m "docs: update architecture documentation"
git commit -m "test: add unit tests for retrieve_node"
```

**Commit Message Format**:
```
<type>: <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with these specifics:

```python
# Good
def retrieve_documents(query: str, top_k: int = 3) -> list[Document]:
    """
    Retrieve relevant documents from vector store.

    Args:
        query: User question to search for
        top_k: Number of documents to return

    Returns:
        List of relevant document objects
    """
    documents = retriever.get_relevant_documents(query)
    return documents[:top_k]

# Bad
def retrieve(q, k=3):
    docs = retriever.get_relevant_documents(q)
    return docs[:k]
```

### Code Formatting

Use **Black** for automatic formatting:

```bash
# Format all files
black .

# Check without modifying
black --check .
```

### Type Hints

Always use type hints:

```python
from typing import TypedDict, Annotated, Sequence

class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add]
    context: str
    question: str

def process_message(message: str) -> dict[str, str]:
    return {"response": message.upper()}
```

### Documentation

Use Google-style docstrings:

```python
def generate_response(context: str, question: str) -> str:
    """
    Generate AI response using LLM.

    Args:
        context: Retrieved context from vector store
        question: User's question

    Returns:
        Generated response text

    Raises:
        ValueError: If context or question is empty
        APIError: If OpenAI API call fails

    Example:
        >>> context = "John has 8 years experience..."
        >>> question = "How many years of experience?"
        >>> generate_response(context, question)
        "I have 8 years of experience..."
    """
    if not context or not question:
        raise ValueError("Context and question must not be empty")

    # Implementation
    ...
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/
│   ├── test_lambda_function.py
│   ├── test_rag_pipeline.py
│   └── test_utils.py
├── integration/
│   ├── test_localstack.py
│   └── test_api_gateway.py
└── fixtures/
    ├── sample_resume.md
    └── mock_responses.json
```

### Writing Tests

```python
import pytest
from unittest.mock import Mock, patch
from lambda_function import retrieve_node, generate_node, GraphState

@pytest.fixture
def mock_retriever():
    """Mock retriever for testing."""
    retriever = Mock()
    retriever.get_relevant_documents.return_value = [
        Mock(page_content="Test content", metadata={"Header 2": "Experience"})
    ]
    return retriever

def test_retrieve_node_returns_context(mock_retriever):
    """Test that retrieve_node returns formatted context."""
    state = GraphState(messages=[], context="", question="What is your experience?")

    with patch('lambda_function.retriever', mock_retriever):
        result = retrieve_node(state)

    assert "context" in result
    assert "Test content" in result["context"]
    mock_retriever.get_relevant_documents.assert_called_once()

def test_retrieve_node_handles_empty_results():
    """Test retrieve_node with no matching documents."""
    # Implementation
    ...
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_lambda_function.py

# Run specific test
pytest tests/unit/test_lambda_function.py::test_retrieve_node_returns_context

# Run integration tests only
pytest tests/integration/
```

### Integration Testing with LocalStack

```bash
# Start LocalStack
make localstack-up

# Deploy
make localstack-deploy

# Run integration tests
pytest tests/integration/

# Cleanup
make localstack-down
```

## Pull Request Process

### Before Submitting

- [ ] All tests pass
- [ ] Code is formatted with Black
- [ ] Type hints are added
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] Branch is up to date with main

```bash
# Update your branch
git fetch upstream
git rebase upstream/main
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe how you tested these changes

## Checklist
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No new warnings

## Related Issues
Fixes #123
```

### Review Process

1. Automated checks must pass (CI/CD)
2. At least one maintainer review required
3. All comments must be addressed
4. Changes should be squashed into logical commits

## Documentation

### Updating Documentation

When adding features, update:

1. **README.md** - User-facing features
2. **ARCHITECTURE.md** - Technical details
3. **QUICKSTART.md** - Setup instructions (if affected)
4. **Code comments** - Complex logic
5. **Docstrings** - All public functions

### Documentation Style

- Use clear, concise language
- Include code examples
- Add diagrams for complex flows
- Keep formatting consistent

## Areas for Contribution

### High Priority

- [ ] Unit tests for RAG pipeline
- [ ] Integration tests for AWS deployment
- [ ] Performance benchmarking suite
- [ ] Error handling improvements
- [ ] Caching implementation

### Medium Priority

- [ ] Multi-language support
- [ ] Alternative LLM providers
- [ ] Conversation history persistence
- [ ] Analytics and monitoring
- [ ] Custom embeddings models

### Low Priority

- [ ] UI themes
- [ ] Voice input support
- [ ] Export chat history
- [ ] Mobile app wrapper
- [ ] Browser extension

## Questions?

- **GitHub Discussions**: For general questions
- **GitHub Issues**: For bug reports and feature requests
- **Email**: maintainer@example.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Virtual Me! 🎉
