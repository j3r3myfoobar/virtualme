"""
Virtual Me Chatbot - AWS Lambda Handler

Main entry point for the Lambda function. Delegates to the RAG pipeline.
"""

import json
from typing import Dict, Any
from pydantic import ValidationError

from rag.pipeline import run_rag_pipeline
from utils.http import http_response
from utils.logging import get_logger
from models.requests import ChatRequest, ErrorResponse
from constants import MIN_REMAINING_TIME_MS, CONVERSATION_TRUNCATE_LIMIT

logger = get_logger(__name__)


def extract_last_user_message(messages: list) -> str:
    """
    Extract the last user message from a conversation history.

    Args:
        messages: List of message dicts with 'role' and 'text' fields

    Returns:
        The text of the last user message, or empty string if none found

    Example:
        >>> messages = [{'role': 'user', 'text': 'Hello'}]
        >>> extract_last_user_message(messages)
        'Hello'
    """
    # Find last message from user
    for message in reversed(messages):
        if message.get('role') == 'user':
            text = message.get('text', '')
            return text.strip()

    return ''


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main AWS Lambda handler function.

    Processes POST requests from Deep Chat frontend with conversation history.
    Extracts the latest user message and runs it through the RAG pipeline.

    Args:
        event: API Gateway event containing request data
        context: Lambda context object

    Returns:
        HTTP response with AI-generated answer

    Example event:
        {
            'body': '{"messages": [{"role": "user", "text": "Hello"}]}',
            'requestContext': {'http': {'method': 'POST'}}
        }
    """

    # Handle CORS preflight requests
    if event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
        return http_response(200, {'message': 'OK'})

    try:
        # Parse and validate request body
        body = json.loads(event.get('body', '{}'))

        # Validate request with Pydantic
        try:
            chat_request = ChatRequest(**body)
        except ValidationError as e:
            # Return detailed validation errors
            error_response = ErrorResponse(
                error="Invalid request format",
                details=e.errors()
            )
            return http_response(422, error_response.model_dump())

        # Truncate conversation to last N messages (silently drop older ones)
        messages = chat_request.messages
        if len(messages) > CONVERSATION_TRUNCATE_LIMIT:
            logger.info("Truncating conversation from %d to %d messages", len(messages), CONVERSATION_TRUNCATE_LIMIT)
            messages = messages[-CONVERSATION_TRUNCATE_LIMIT:]

        # Extract the last user message
        last_user_message = messages[-1].text

        logger.info("Processing question: %s...", last_user_message[:100])

        # Check remaining execution time before starting expensive RAG pipeline
        if context is not None:
            remaining_ms = context.get_remaining_time_in_millis()
            if remaining_ms < MIN_REMAINING_TIME_MS:
                logger.warning("Insufficient time remaining: %dms < %dms", remaining_ms, MIN_REMAINING_TIME_MS)
                return http_response(503, {
                    'error': 'Insufficient time remaining',
                    'retry': True
                })

        # Run the RAG pipeline
        answer = run_rag_pipeline(last_user_message)

        logger.info("Generated answer (%d chars)", len(answer))

        # Format response for Deep Chat
        response_body = {
            'text': answer
        }

        return http_response(200, response_body)

    except json.JSONDecodeError as e:
        logger.warning("Invalid JSON: %s", e)
        return http_response(400, {'error': 'Invalid JSON in request body'})

    except ValueError as e:
        logger.warning("Validation error: %s", e)
        return http_response(400, {'error': str(e)})

    except Exception:
        logger.exception("Unexpected error in lambda handler")
        return http_response(500, {
            'error': 'Internal server error'
        })


# ============================================================================
# LOCAL TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Local testing script. Set OPENAI_API_KEY environment variable before running.

    Usage:
        export OPENAI_API_KEY="sk-proj-xxx"
        cd src
        python lambda_function.py
    """
    print("=" * 60)
    print("Virtual Me Chatbot - Local Test")
    print("=" * 60)

    # Mock event for testing
    test_event = {
        'body': json.dumps({
            'messages': [
                {'role': 'user', 'text': 'What is your main area of expertise?'}
            ]
        }),
        'requestContext': {
            'http': {'method': 'POST'}
        }
    }

    print("\nProcessing test request...")
    response = lambda_handler(test_event, None)

    print("\n" + "=" * 60)
    print("Test Response")
    print("=" * 60)
    print(f"Status Code: {response['statusCode']}")
    print(f"\nBody:")
    print(json.dumps(json.loads(response['body']), indent=2))
    print("=" * 60)
