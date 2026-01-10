"""
Configuration for LLM backends and models using Pydantic settings.

Supports multiple backends:
- Bedrock (production deployment)
- LM Studio (local development/testing)
"""

import os
from typing import Literal, Optional, Dict, Set
from pydantic import BaseModel, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from constants import DEFAULT_LLM_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, DEFAULT_AWS_REGION
from utils.logging import get_logger

logger = get_logger(__name__)

# Backend types
LLMBackend = Literal["bedrock", "lm_studio"]
EmbeddingBackend = Literal["bedrock", "openai"]


# Model availability by region prefix
# Models with "eu." prefix are available in EU regions
# Models with "us." prefix are available in US regions
# Models without prefix are generally available
MODEL_REGION_MAP: Dict[str, Set[str]] = {
    # EU-available models (eu-west-1, eu-west-3, etc.)
    "eu.meta.llama3-2-1b-instruct-v1:0": {"eu-west-1", "eu-west-3", "eu-central-1"},
    "eu.meta.llama3-2-3b-instruct-v1:0": {"eu-west-1", "eu-west-3", "eu-central-1"},
    # US-only models
    "us.meta.llama3-2-8b-instruct-v1:0": {"us-east-1", "us-west-2"},
    # Generally available models (most regions)
    "mistral.mixtral-8x7b-instruct-v0:1": {"us-east-1", "us-west-2", "eu-west-1", "eu-west-3", "ap-northeast-1"},
    "mistral.mistral-7b-instruct-v0:2": {"us-east-1", "us-west-2", "eu-west-1", "eu-west-3"},
    "amazon.titan-text-lite-v1": {"us-east-1", "us-west-2", "eu-west-1", "eu-west-3", "ap-northeast-1"},
    "amazon.titan-text-express-v1": {"us-east-1", "us-west-2", "eu-west-1", "eu-west-3", "ap-northeast-1"},
}

# Available Bedrock models (alias -> model_id)
BEDROCK_MODELS: Dict[str, str] = {
    # Amazon Nova 2 models (re:Invent 2025) - cross-region inference
    "nova-2-lite": "eu.amazon.nova-2-lite-v1:0",
    "nova-2-pro": "eu.amazon.nova-2-pro-v1:0",

    # Llama models (Meta) - EU inference profiles for eu-west-3
    "llama-3.2-1b": "eu.meta.llama3-2-1b-instruct-v1:0",
    "llama-3.2-3b": "eu.meta.llama3-2-3b-instruct-v1:0",
    "llama-3.2-8b": "us.meta.llama3-2-8b-instruct-v1:0",
    "llama-3.1-8b": "meta.llama3-1-8b-instruct-v1:0",
    "llama-3.1-70b": "meta.llama3-1-70b-instruct-v1:0",

    # Claude models (Anthropic)
    "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
    "claude-3-sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
    "claude-3.5-sonnet": "anthropic.claude-3-5-sonnet-20240620-v1:0",

    # Mistral models (legacy)
    "mistral-7b": "mistral.mistral-7b-instruct-v0:2",
    "mixtral-8x7b": "mistral.mixtral-8x7b-instruct-v0:1",

    # Amazon Titan
    "titan-text-lite": "amazon.titan-text-lite-v1",
    "titan-text-express": "amazon.titan-text-express-v1",
}

# Bedrock embedding models
BEDROCK_EMBEDDING_MODELS: Dict[str, str] = {
    "titan-embed-text-v1": "amazon.titan-embed-text-v1",
    "titan-embed-text-v2": "amazon.titan-embed-text-v2:0",
    "cohere-embed-english": "cohere.embed-english-v3",
    "cohere-embed-multilingual": "cohere.embed-multilingual-v3",
}


class ModelConfig(BaseModel):
    """Configuration for LLM model with validation."""
    backend: LLMBackend
    model_id: str
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: Optional[int] = DEFAULT_MAX_TOKENS
    aws_region: str = DEFAULT_AWS_REGION
    lm_studio_base_url: str = "http://localhost:1234/v1"

    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Ensure temperature is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Temperature must be between 0.0 and 1.0, got {v}")
        return v

    @model_validator(mode='after')
    def validate_model_region(self) -> 'ModelConfig':
        """Warn if model may not be available in selected region."""
        if self.backend == "bedrock" and self.model_id in MODEL_REGION_MAP:
            available_regions = MODEL_REGION_MAP[self.model_id]
            if self.aws_region not in available_regions:
                logger.warning(
                    "Model %s may not be available in region %s. "
                    "Available regions: %s",
                    self.model_id, self.aws_region, ", ".join(sorted(available_regions))
                )
        return self


class EmbeddingConfig(BaseModel):
    """Configuration for embedding model."""
    backend: EmbeddingBackend
    model_id: str
    aws_region: str = DEFAULT_AWS_REGION


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment Variables:
        LLM_BACKEND: Backend to use (bedrock, lm_studio)
        LLM_MODEL: Model identifier or alias
        LLM_TEMPERATURE: Sampling temperature (0.0-1.0)
        AWS_DEFAULT_REGION: AWS region for Bedrock
        LM_STUDIO_BASE_URL: Base URL for LM Studio
        EMBEDDING_BACKEND: Embedding backend (bedrock, openai)
        EMBEDDING_MODEL: Embedding model identifier
    """
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore"
    )

    # LLM settings
    llm_backend: LLMBackend = "bedrock"
    llm_model: str = DEFAULT_LLM_MODEL
    llm_temperature: float = DEFAULT_TEMPERATURE

    # AWS settings
    aws_default_region: str = DEFAULT_AWS_REGION
    aws_region: Optional[str] = None  # Fallback

    # LM Studio settings
    lm_studio_base_url: str = "http://localhost:1234/v1"

    # Embedding settings
    embedding_backend: EmbeddingBackend = "bedrock"
    embedding_model: str = "titan-embed-text-v2"

    @property
    def effective_region(self) -> str:
        """Get effective AWS region (AWS_DEFAULT_REGION takes priority)."""
        return self.aws_default_region or self.aws_region or DEFAULT_AWS_REGION


# Global settings instance (lazy loaded)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def _resolve_model_id(alias: str, model_map: Dict[str, str], is_bedrock: bool) -> str:
    """
    Resolve model alias to full model ID.

    Args:
        alias: Model alias or direct model ID
        model_map: Mapping of aliases to model IDs
        is_bedrock: Whether this is a Bedrock backend

    Returns:
        Resolved model ID
    """
    if is_bedrock:
        return model_map.get(alias, alias)
    return alias


def get_model_config() -> ModelConfig:
    """
    Get model configuration from environment variables.

    Returns:
        ModelConfig instance with validated settings
    """
    settings = get_settings()
    model_id = _resolve_model_id(
        settings.llm_model,
        BEDROCK_MODELS,
        settings.llm_backend == "bedrock"
    )

    return ModelConfig(
        backend=settings.llm_backend,
        model_id=model_id,
        temperature=settings.llm_temperature,
        aws_region=settings.effective_region,
        lm_studio_base_url=settings.lm_studio_base_url
    )


def get_embedding_config() -> Dict[str, str]:
    """
    Get embedding configuration from environment variables.

    Returns:
        Dict with backend, model_id, and aws_region
    """
    settings = get_settings()
    model_id = _resolve_model_id(
        settings.embedding_model,
        BEDROCK_EMBEDDING_MODELS,
        settings.embedding_backend == "bedrock"
    )

    return {
        "backend": settings.embedding_backend,
        "model_id": model_id,
        "aws_region": settings.effective_region
    }


def list_available_models(backend: LLMBackend = "bedrock") -> Dict[str, str]:
    """
    List available models for a backend.

    Args:
        backend: Backend name

    Returns:
        Dict of model aliases to model IDs
    """
    if backend == "bedrock":
        return BEDROCK_MODELS.copy()
    elif backend == "lm_studio":
        return {"local-model": "Local model in LM Studio (check LM Studio UI)"}
    return {}


def reset_settings() -> None:
    """Reset settings cache (useful for testing)."""
    global _settings
    _settings = None
