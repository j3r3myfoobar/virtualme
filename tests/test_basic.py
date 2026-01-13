"""
Basic tests for the Virtual Me RAG chatbot.

Simple, readable tests that demonstrate how the system works.
Run with: python3 -m pytest tests/test_basic.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from models.requests import ChatRequest, Message
from pydantic import ValidationError


def test_valid_chat_request():
    """Test that a valid chat request is accepted."""
    request = ChatRequest(
        messages=[
            Message(role="user", text="What is your experience?")
        ]
    )

    assert len(request.messages) == 1
    assert request.messages[0].role == "user"
    assert request.messages[0].text == "What is your experience?"


def test_empty_message_rejected():
    """Test that empty messages are rejected."""
    try:
        Message(role="user", text="   ")  # Whitespace only
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass  # Expected


def test_last_message_must_be_user():
    """Test that the last message must be from the user."""
    try:
        ChatRequest(
            messages=[
                Message(role="user", text="Hello"),
                Message(role="ai", text="Hi there!")  # Last message is AI
            ]
        )
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "Last message must be from user" in str(e)


def test_message_length_limits():
    """Test that messages respect length limits."""
    # Too long message (>5000 chars)
    try:
        Message(role="user", text="x" * 6000)
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass  # Expected

    # Valid length message
    msg = Message(role="user", text="x" * 100)
    assert len(msg.text) == 100


if __name__ == "__main__":
    """Run tests with simple assertions."""
    print("Running basic tests...\n")

    test_valid_chat_request()
    print("✓ test_valid_chat_request passed")

    test_empty_message_rejected()
    print("✓ test_empty_message_rejected passed")

    test_last_message_must_be_user()
    print("✓ test_last_message_must_be_user passed")

    test_message_length_limits()
    print("✓ test_message_length_limits passed")

    print("\n✅ All tests passed!")
