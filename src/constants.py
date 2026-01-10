"""
Configuration constants for Virtual Me chatbot.

Centralizes all hardcoded values for easier maintenance and configuration.
"""

from pathlib import Path

# ==============================================================================
# Paths
# ==============================================================================

SRC_DIR = Path(__file__).parent
KNOWLEDGE_BASE_DIR = SRC_DIR / "knowledge_base"
PROMPTS_DIR = SRC_DIR / "prompts"

# Legacy single file path (for backward compatibility)
RESUME_PATH = SRC_DIR / "resume.md"

# ==============================================================================
# LLM Configuration
# ==============================================================================

# Default model for production (Bedrock)
DEFAULT_LLM_MODEL = "nova-2-lite"

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
# 1000 chars is plenty for a question (typical: 50-200 chars)
MAX_MESSAGE_LENGTH = 1000

# Maximum number of messages accepted in request (prevent abuse)
MAX_CONVERSATION_LENGTH = 100

# Number of recent messages to keep when processing (server-side truncation)
# Older messages are silently dropped - only last N are used
CONVERSATION_TRUNCATE_LIMIT = 20

# Warn when conversation history exceeds this threshold
CONVERSATION_WARNING_THRESHOLD = 15

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
# Lambda Configuration
# ==============================================================================

# Minimum time required for RAG pipeline (milliseconds)
# If remaining Lambda execution time is below this, return 503 to allow retry
MIN_REMAINING_TIME_MS = 10000

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
