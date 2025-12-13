"""
LLM-based response generator with multiple backend support.

Supports:
- AWS Bedrock (Llama, Claude, Mistral, Titan)
- LM Studio (local development)
- OpenAI (legacy support)
"""

import os
from typing import Optional
from langchain_core.messages import HumanMessage
from langchain_core.language_models import BaseChatModel

# Relative imports (IntelliJ-friendly)
from ..config import get_model_config, ModelConfig


# System prompt that defines the chatbot's persona and constraints
SYSTEM_PROMPT = """You are a Virtual Clone chatbot representing the person described in the provided context.

CRITICAL RULES:
1. Answer ONLY based on the provided CONTEXT below
2. If the question cannot be answered from the CONTEXT, say: "I don't have that information in my profile."
3. Respond in first person as if you ARE the person in the resume
4. Be conversational, friendly, and professional
5. Never make up or hallucinate information not present in the CONTEXT
6. Keep responses concise (2-4 sentences unless more detail is explicitly requested)

CONTEXT:
{context}

Remember: You are speaking AS this person, not ABOUT them."""


def _get_llm(config: ModelConfig) -> BaseChatModel:
    """
    Get LLM instance based on configuration.

    Args:
        config: Model configuration

    Returns:
        Configured LLM instance

    Raises:
        ValueError: If backend is not supported or credentials missing
    """
    if config.backend == "bedrock":
        try:
            from langchain_aws import ChatBedrock
        except ImportError:
            raise ImportError(
                "langchain-aws not installed. Install with: pip install langchain-aws"
            )

        print(f"Using Bedrock model: {config.model_id}")

        return ChatBedrock(
            model_id=config.model_id,
            region_name=config.aws_region,
            model_kwargs={
                "temperature": config.temperature,
                "max_tokens": config.max_tokens or 2048,
            }
        )

    elif config.backend == "lm_studio":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai not installed. Install with: pip install langchain-openai"
            )

        print(f"Using LM Studio model: {config.model_id}")

        return ChatOpenAI(
            base_url=config.lm_studio_base_url,
            api_key="lm-studio",  # LM Studio doesn't require real API key
            model=config.model_id,
            temperature=config.temperature,
        )

    elif config.backend == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai not installed. Install with: pip install langchain-openai"
            )

        api_key = config.openai_api_key or os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set for OpenAI backend")

        print(f"Using OpenAI model: {config.model_id}")

        return ChatOpenAI(
            model=config.model_id,
            temperature=config.temperature,
            openai_api_key=api_key
        )

    else:
        raise ValueError(f"Unsupported backend: {config.backend}")


def generate_response(
    context: str,
    question: str,
    config: Optional[ModelConfig] = None
) -> str:
    """
    Generate response using LLM based on retrieved context.

    Args:
        context: Retrieved context from vector store
        question: User's question
        config: Model configuration (defaults to environment-based config)

    Returns:
        Generated response text

    Raises:
        ValueError: If context or question is empty
        Exception: If LLM call fails

    Example:
        >>> # Using default config (from environment)
        >>> context = "I have 8 years of experience..."
        >>> question = "How many years of experience?"
        >>> response = generate_response(context, question)

        >>> # Using custom config
        >>> from config import ModelConfig
        >>> config = ModelConfig(backend="bedrock", model_id="llama-3.2-8b")
        >>> response = generate_response(context, question, config)
    """
    # Validate inputs
    if not context:
        raise ValueError("Context cannot be empty")
    if not question:
        raise ValueError("Question cannot be empty")

    # Get configuration
    if config is None:
        config = get_model_config()

    # Get LLM instance
    llm = _get_llm(config)

    # Format the full prompt
    prompt = SYSTEM_PROMPT.format(context=context)

    # Generate response
    messages = [
        HumanMessage(content=prompt),
        HumanMessage(content=f"Question: {question}")
    ]

    print(f"Generating response using {config.backend}...")
    response = llm.invoke(messages)

    return response.content


def update_system_prompt(new_prompt: str) -> None:
    """
    Update the system prompt.

    Useful for customizing the chatbot's behavior.

    Args:
        new_prompt: New system prompt template (must contain {context} placeholder)

    Raises:
        ValueError: If prompt doesn't contain {context} placeholder
    """
    global SYSTEM_PROMPT

    if "{context}" not in new_prompt:
        raise ValueError("System prompt must contain {context} placeholder")

    SYSTEM_PROMPT = new_prompt
    print("System prompt updated")
