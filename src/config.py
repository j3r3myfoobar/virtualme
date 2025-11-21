"""
Configuration for LLM backends and models.

Supports multiple backends:
- Bedrock (production)
- LM Studio (local development)
- OpenAI (legacy support)
"""

import os
from typing import Literal, Optional
from dataclasses import dataclass


# Backend types
LLMBackend = Literal["bedrock", "lm_studio", "openai"]


@dataclass
class ModelConfig:
    """Configuration for LLM model."""
    backend: LLMBackend
    model_id: str
    temperature: float = 0.3
    max_tokens: Optional[int] = None
    # Backend-specific settings
    aws_region: str = "us-east-1"
    lm_studio_base_url: str = "http://localhost:1234/v1"
    openai_api_key: Optional[str] = None


# Available Bedrock models
BEDROCK_MODELS = {
    # Llama models (Meta)
    "llama-3.2-1b": "meta.llama3-2-1b-instruct-v1:0",
    "llama-3.2-3b": "meta.llama3-2-3b-instruct-v1:0",
    "llama-3.2-8b": "us.meta.llama3-2-8b-instruct-v1:0",
    "llama-3.1-8b": "meta.llama3-1-8b-instruct-v1:0",
    "llama-3.1-70b": "meta.llama3-1-70b-instruct-v1:0",

    # Claude models (Anthropic)
    "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
    "claude-3-sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
    "claude-3.5-sonnet": "anthropic.claude-3-5-sonnet-20240620-v1:0",

    # Mistral models
    "mistral-7b": "mistral.mistral-7b-instruct-v0:2",
    "mixtral-8x7b": "mistral.mixtral-8x7b-instruct-v0:1",

    # Amazon Titan
    "titan-text-lite": "amazon.titan-text-lite-v1",
    "titan-text-express": "amazon.titan-text-express-v1",
}


# Bedrock embedding models
BEDROCK_EMBEDDING_MODELS = {
    "titan-embed-text-v1": "amazon.titan-embed-text-v1",
    "titan-embed-text-v2": "amazon.titan-embed-text-v2:0",
    "cohere-embed-english": "cohere.embed-english-v3",
    "cohere-embed-multilingual": "cohere.embed-multilingual-v3",
}


def get_model_config() -> ModelConfig:
    """
    Get model configuration from environment variables.

    Environment Variables:
        LLM_BACKEND: Backend to use (bedrock, lm_studio, openai)
        LLM_MODEL: Model identifier
        LLM_TEMPERATURE: Sampling temperature (0.0-1.0)
        AWS_REGION: AWS region for Bedrock
        LM_STUDIO_BASE_URL: Base URL for LM Studio
        OPENAI_API_KEY: OpenAI API key (if using OpenAI)

    Returns:
        ModelConfig instance

    Examples:
        # Production (Bedrock)
        LLM_BACKEND=bedrock LLM_MODEL=llama-3.2-8b

        # Local development (LM Studio)
        LLM_BACKEND=lm_studio LLM_MODEL=llama-3.2-3b

        # Legacy (OpenAI)
        LLM_BACKEND=openai OPENAI_API_KEY=sk-xxx
    """
    backend = os.environ.get("LLM_BACKEND", "bedrock").lower()
    model = os.environ.get("LLM_MODEL", "llama-3.2-3b")
    temperature = float(os.environ.get("LLM_TEMPERATURE", "0.3"))
    aws_region = os.environ.get("AWS_REGION", "us-east-1")
    lm_studio_url = os.environ.get("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
    openai_key = os.environ.get("OPENAI_API_KEY")

    # Resolve model ID based on backend
    if backend == "bedrock":
        model_id = BEDROCK_MODELS.get(model, model)
    else:
        model_id = model

    return ModelConfig(
        backend=backend,
        model_id=model_id,
        temperature=temperature,
        aws_region=aws_region,
        lm_studio_base_url=lm_studio_url,
        openai_api_key=openai_key
    )


def get_embedding_config() -> dict:
    """
    Get embedding configuration from environment variables.

    Environment Variables:
        EMBEDDING_BACKEND: Backend to use (bedrock, openai)
        EMBEDDING_MODEL: Model identifier

    Returns:
        Dict with backend and model_id
    """
    backend = os.environ.get("EMBEDDING_BACKEND", "bedrock").lower()
    model = os.environ.get("EMBEDDING_MODEL", "titan-embed-text-v2")

    if backend == "bedrock":
        model_id = BEDROCK_EMBEDDING_MODELS.get(model, model)
    else:
        model_id = model

    return {
        "backend": backend,
        "model_id": model_id,
        "aws_region": os.environ.get("AWS_REGION", "us-east-1")
    }


def list_available_models(backend: LLMBackend = "bedrock") -> dict:
    """
    List available models for a backend.

    Args:
        backend: Backend name

    Returns:
        Dict of model aliases to model IDs
    """
    if backend == "bedrock":
        return BEDROCK_MODELS
    elif backend == "lm_studio":
        return {
            "local-model": "Local model in LM Studio (check LM Studio UI)"
        }
    elif backend == "openai":
        return {
            "gpt-4o-mini": "gpt-4o-mini",
            "gpt-4o": "gpt-4o",
            "gpt-4": "gpt-4-turbo"
        }
    else:
        return {}
