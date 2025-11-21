"""
LLM-based response generator.

Handles calling OpenAI GPT-4o-mini with retrieved context
to generate grounded responses.
"""

import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage


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


def generate_response(
    context: str,
    question: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    api_key: Optional[str] = None
) -> str:
    """
    Generate response using LLM based on retrieved context.

    Args:
        context: Retrieved context from vector store
        question: User's question
        model: OpenAI model to use (default: gpt-4o-mini)
        temperature: Sampling temperature 0.0-1.0 (lower = more factual)
        api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)

    Returns:
        Generated response text

    Raises:
        ValueError: If context or question is empty, or API key not set
        Exception: If LLM call fails

    Example:
        >>> context = "I have 8 years of experience in cloud computing..."
        >>> question = "How many years of experience do you have?"
        >>> response = generate_response(context, question)
        >>> "8 years" in response
        True
    """
    # Validate inputs
    if not context:
        raise ValueError("Context cannot be empty")
    if not question:
        raise ValueError("Question cannot be empty")

    # Get API key
    if api_key is None:
        api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Initialize the LLM
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,  # Low temperature for more factual responses
        openai_api_key=api_key
    )

    # Format the full prompt
    prompt = SYSTEM_PROMPT.format(context=context)

    # Generate response
    messages = [
        HumanMessage(content=prompt),
        HumanMessage(content=f"Question: {question}")
    ]

    print(f"Generating response with {model} (temp={temperature})...")
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
