"""
Configuration constants for Virtual Me chatbot.

Centralizes all hardcoded values for easier maintenance and configuration.
"""

from pathlib import Path

# ==============================================================================
# Paths
# ==============================================================================

SRC_DIR = Path(__file__).parent
RESUME_PATH = SRC_DIR / "resume.md"
PROMPTS_DIR = SRC_DIR / "prompts"

# ==============================================================================
# LLM Configuration
# ==============================================================================

# Default model for production (Bedrock)
DEFAULT_LLM_MODEL = "mixtral-8x7b"

# Temperature for response generation
# Lower = more factual/deterministic, Higher = more creative
# 0.1 recommended for factual chatbots to minimize hallucination
DEFAULT_TEMPERATURE = 0.1

# Maximum tokens for LLM response
DEFAULT_MAX_TOKENS = 2048

# ==============================================================================
# Message Validation Limits
# ==============================================================================

# Maximum length for a single message (characters)
# Balances user input flexibility vs token cost
MAX_MESSAGE_LENGTH = 5000

# Maximum number of messages in conversation history
# Prevents context overflow and excessive token usage
MAX_CONVERSATION_LENGTH = 50

# Warn when conversation history exceeds this threshold
# May impact response quality due to context length
CONVERSATION_WARNING_THRESHOLD = 20

# ==============================================================================
# RAG Configuration
# ==============================================================================

# Number of document chunks to retrieve for context
# More chunks = better context but slower response and higher cost
RAG_TOP_K_CHUNKS = 3

# Markdown header levels to split on
# Maintains hierarchical context from resume structure
MARKDOWN_HEADERS_TO_SPLIT = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

# ==============================================================================
# AWS Configuration
# ==============================================================================

# Default AWS region for resources
DEFAULT_AWS_REGION = "eu-west-3"

# ==============================================================================
# CORS Configuration
# ==============================================================================

# Allowed origins for CORS
# '*' allows all origins (use specific domains in production)
ALLOWED_ORIGINS = ["https://chat.lemaire.tel"]

# Allowed HTTP methods
ALLOWED_METHODS = ["OPTIONS", "POST"]

# Allowed headers
ALLOWED_HEADERS = ["content-type"]

# CORS max age (seconds)
CORS_MAX_AGE = 300

# ==============================================================================
# HTTP Response
# ==============================================================================

# Default content type for API responses
CONTENT_TYPE = "application/json"

# ==============================================================================
# Logging
# ==============================================================================

# Enable debug logging
DEBUG_MODE = False
