"""Unit tests for Lambda handler."""

import json
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from lambda_function import extract_last_user_message


def test_extract_last_user_message():
    """Test extracting last user message from conversation."""
    messages = [
        {'role': 'user', 'text': 'Hello'},
        {'role': 'ai', 'text': 'Hi there'},
        {'role': 'user', 'text': 'How are you?'}
    ]

    result = extract_last_user_message(messages)
    assert result == 'How are you?'


def test_extract_last_user_message_empty():
    """Test with no user messages."""
    messages = [
        {'role': 'ai', 'text': 'Hello'}
    ]

    result = extract_last_user_message(messages)
    assert result == ''


def test_extract_last_user_message_whitespace():
    """Test that whitespace is stripped."""
    messages = [
        {'role': 'user', 'text': '  What is your name?  '}
    ]

    result = extract_last_user_message(messages)
    assert result == 'What is your name?'


if __name__ == '__main__':
    print("Running Lambda handler tests...")
    test_extract_last_user_message()
    test_extract_last_user_message_empty()
    test_extract_last_user_message_whitespace()
    print("✓ All tests passed!")
